# routes.py
"""
Módulo de rutas y endpoints de la API de reservas de peluquería.
Incluye endpoints para servicios, profesionales, slots y reservas.
"""

from __future__ import annotations
from datetime import datetime, timedelta, time
import os
import uuid
import logging

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlmodel import Session, select

from data import (
    SERVICES, PROS, SERVICE_BY_ID, PRO_BY_ID,
)
from models import (
    SlotsQuery, SlotsOut,
    Reservation, CancelReservationIn, ActionResult,
    RescheduleIn, RescheduleOut, ReservationIn,
    ReservationDB,
)
from logic import (
    find_available_slots,
    find_reservation, cancel_reservation,
    apply_reschedule,
    create_gcal_reservation,
    patch_gcal_reservation,
    delete_gcal_reservation,
    get_calendar_for_professional,
)
from db import get_session, engine

from utils.date import validate_target_dt, TZ
from datetime import timezone as _utc_tz

logger = logging.getLogger("pelubot.api")

# --- Seguridad por API Key ---
API_KEY = os.getenv("API_KEY", "changeme")  # Cambia en producción
ALLOW_LOCAL_NO_AUTH = os.getenv("ALLOW_LOCAL_NO_AUTH", "false").lower() in ("1","true","yes","y","si","sí")

def require_api_key(request: Request):
    # Bypass opcional para desarrollo local
    client_host = getattr(request.client, "host", None)
    if ALLOW_LOCAL_NO_AUTH and client_host in ("127.0.0.1", "localhost"):
        return
    # X-API-Key directo
    key = request.headers.get("X-API-Key") or ""
    # Authorization: Bearer <token>
    auth = request.headers.get("Authorization") or ""
    if not key and auth:
        parts = auth.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            key = parts[1].strip()
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

router = APIRouter()

# ID de calendario configurable por entorno (fallback al test)
GCAL_CALENDAR_ID = os.getenv("GCAL_CALENDAR_ID", os.getenv("GCAL_TEST_CALENDAR_ID", "pelubot.test@gmail.com"))

# ---------------------
# Endpoints de salud y home
# ---------------------
@router.get("/health")
def health():
    """Endpoint de salud para comprobar que la API está activa."""
    return {"ok": True}

@router.get("/ready", tags=["monitor"])
def readiness():
    """Comprueba dependencias internas: DB y Google Calendar (cliente)."""
    status = {"db": "ok", "gcal": "ok"}
    # DB check
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception as e:
        status["db"] = f"error: {e}"
    # Google Calendar client check (sin llamada de red)
    try:
        from google_calendar import build_calendar
        _ = build_calendar()
    except Exception as e:
        status["gcal"] = f"error: {e}"

    ok = all(v == "ok" for v in status.values())
    return {"ok": ok, **status}

@router.get("/")
def home():
    """Endpoint raíz con información de rutas disponibles."""
    return {
        "status": "ok",
        "try": [
            "/health", "/docs",
            "/services", "/professionals", "/slots",
            "/reservations", "/cancel_reservation (POST)",
            "/reservations/{reservation_id} (DELETE)",
            "/reschedule (POST)",
        ],
    }

# ---------------------
# Catálogos & Estado
# ---------------------
@router.get("/services")
def list_services():
    """Lista los servicios disponibles en la peluquería."""
    return SERVICES

@router.get("/professionals")
def list_professionals():
    """Lista los profesionales disponibles en la peluquería."""
    return PROS

@router.get("/reservations")
def list_reservations(session: Session = Depends(get_session)):
    """Lista reservas persistidas en la base de datos."""
    rows = session.exec(select(ReservationDB).order_by(ReservationDB.start)).all()
    logger.info("List reservations: %s rows", len(rows))
    out = []
    for r in rows:
        created = r.created_at
        updated = getattr(r, "updated_at", None)
        if created is not None and created.tzinfo is None:
            created = created.replace(tzinfo=_utc_tz.utc)
        if updated is not None and updated.tzinfo is None:
            updated = updated.replace(tzinfo=_utc_tz.utc)
        out.append({
            "id": r.id,
            "service_id": r.service_id,
            "professional_id": r.professional_id,
            "start": r.start.isoformat() if hasattr(r.start, "isoformat") else r.start,
            "end": r.end.isoformat() if hasattr(r.end, "isoformat") else r.end,
            "google_event_id": r.google_event_id,
            "google_calendar_id": r.google_calendar_id,
            "created_at": created.isoformat() if created else None,
            "updated_at": updated.isoformat() if updated else None,
        })
    return out

# ---------------------
# Cancelar reservas
# ---------------------
@router.post("/cancel_reservation", response_model=ActionResult)
def cancel_reservation_post(
    payload: CancelReservationIn,
    session: Session = Depends(get_session),
    _=Depends(require_api_key),
):
    """Cancela una reserva existente por ID."""
    logger.info("Cancel reservation requested: id=%s", payload.reservation_id)
    r = find_reservation(session, payload.reservation_id)
    if not r:
        raise HTTPException(status_code=404, detail="La reserva no existe")

    if r.google_event_id:
        try:
            delete_gcal_reservation(r.google_event_id, r.google_calendar_id or GCAL_CALENDAR_ID)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"No se pudo borrar en Google Calendar: {e}")

    ok = cancel_reservation(session, payload.reservation_id)
    if ok:
        logger.info("Reservation cancelled: id=%s", payload.reservation_id)
        return ActionResult(ok=True, message=f"Reserva {payload.reservation_id} cancelada.")
    raise HTTPException(status_code=500, detail="No se pudo cancelar la reserva")

@router.delete("/reservations/{reservation_id}", response_model=ActionResult)
def cancel_reservation_delete(
    reservation_id: str,
    session: Session = Depends(get_session),
    _=Depends(require_api_key),
):
    """Cancela una reserva existente por ID (DELETE)."""
    logger.info("Cancel reservation requested: id=%s", reservation_id)
    r = find_reservation(session, reservation_id)
    if not r:
        raise HTTPException(status_code=404, detail="La reserva no existe")

    if r.google_event_id:
        try:
            delete_gcal_reservation(r.google_event_id, r.google_calendar_id or GCAL_CALENDAR_ID)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"No se pudo borrar en Google Calendar: {e}")

    ok = cancel_reservation(session, reservation_id)
    if ok:
        logger.info("Reservation cancelled: id=%s", reservation_id)
        return ActionResult(ok=True, message=f"Reserva {reservation_id} cancelada.")
    raise HTTPException(status_code=500, detail="No se pudo cancelar la reserva")

# ---------------------
# Reprogramar (reschedule)
# ---------------------
@router.post("/reschedule", response_model=RescheduleOut)
def reschedule_post(
    payload: RescheduleIn,
    session: Session = Depends(get_session),
    _=Depends(require_api_key),
):
    """
    Reprograma una reserva existente a un nuevo horario.
    Si viene (new_date, new_time), se valida aquí; el resto en logic.apply_reschedule.
    """
    logger.info(
        "Reschedule requested: id=%s new_date=%s new_time=%s new_pro=%s",
        payload.reservation_id, payload.new_date, payload.new_time, payload.professional_id
    )

    r_prev = find_reservation(session, payload.reservation_id)
    if not r_prev:
        raise HTTPException(status_code=404, detail="La reserva no existe")

    # Prevalidación si tenemos fecha/hora nuevas explícitas
    if payload.new_date and payload.new_time:
        try:
            new_start = datetime.strptime(f"{payload.new_date} {payload.new_time}", "%Y-%m-%d %H:%M")
            if new_start.tzinfo is None:
                new_start = new_start.replace(tzinfo=TZ)
            validate_target_dt(new_start)
        except ValueError:
            raise HTTPException(status_code=400, detail="Fecha/hora inválidas (formato).")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    old_start, old_end, old_pro, old_cal = r_prev.start, r_prev.end, r_prev.professional_id, r_prev.google_calendar_id

    ok, msg, r = apply_reschedule(session, payload)
    if not ok or not r:
        raise HTTPException(status_code=400, detail=msg)

    # Garantizar que el mensaje contenga 'Reprogramada' para compatibilidad de tests
    message_out = msg if (isinstance(msg, str) and "Reprogramada" in msg) else f"Reprogramada: {msg}"

    if r.google_event_id:
        try:
            new_cal = get_calendar_for_professional(r.professional_id)
            if old_cal and old_cal != new_cal:
                # Mover de calendario (borra y crea)
                delete_gcal_reservation(r.google_event_id, old_cal)
                gnew = create_gcal_reservation(
                    Reservation(
                        id=r.id, service_id=r.service_id, professional_id=r.professional_id,
                        start=r.start, end=r.end, google_event_id=r.google_event_id, google_calendar_id=new_cal
                    ),
                    calendar_id=new_cal
                )
                r.google_event_id = gnew.get("id")
                r.google_calendar_id = new_cal
            else:
                patch_gcal_reservation(r.google_event_id, r.start, r.end, old_cal or new_cal)
                r.google_calendar_id = old_cal or new_cal

            session.add(r)
            session.commit()
            session.refresh(r)

        except Exception as e:
            # rollback local
            r.start, r.end, r.professional_id, r.google_calendar_id = old_start, old_end, old_pro, old_cal
            session.add(r)
            session.commit()
            raise HTTPException(status_code=502, detail=f"No se pudo reprogramar en Google Calendar: {e}")

    logger.info(
        "Reservation rescheduled: id=%s start=%s end=%s pro=%s",
        r.id, r.start.isoformat(), r.end.isoformat(), r.professional_id
    )
    return RescheduleOut(
        ok=True, message=message_out, reservation_id=r.id,
        start=r.start.isoformat(), end=r.end.isoformat()
    )

# Alias para compatibilidad con tests: /reservations/reschedule
@router.post("/reservations/reschedule", response_model=RescheduleOut)
def reschedule_post_alias(
    payload: RescheduleIn,
    session: Session = Depends(get_session),
    _=Depends(require_api_key),
):
    return reschedule_post(payload, session, _)

# ---------------------
# Slots disponibles
# ---------------------
@router.post("/slots", response_model=SlotsOut)
def get_slots(q: SlotsQuery, session: Session = Depends(get_session)):
    """
    Obtiene los horarios disponibles para un servicio y fecha determinados.
    Valida que la fecha no esté en el pasado ni más allá de 6 meses.
    """
    logger.info("Slots query: service=%s date=%s pro=%s", q.service_id, q.date_str, q.professional_id)
    try:
        d = datetime.strptime(q.date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="date_str debe ser YYYY-MM-DD")

    # Validación de rango en el inicio del día (TZ Madrid)
    day_start = datetime.combine(d, time.min).replace(tzinfo=TZ)
    try:
        validate_target_dt(day_start)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if q.service_id not in SERVICE_BY_ID:
        raise HTTPException(status_code=404, detail="service_id no existe")
    if q.professional_id and q.professional_id not in PRO_BY_ID:
        raise HTTPException(status_code=404, detail="professional_id no existe")

    avail = find_available_slots(
        session,
        q.service_id,
        d,
        q.professional_id,
        use_gcal_busy_override=q.use_gcal,
    )
    return SlotsOut(
        service_id=q.service_id,
        date=d,
        professional_id=q.professional_id,
        slots=[dt.isoformat() for dt in avail],
    )

# ---------------------
# Crear reserva
# ---------------------
# Helper para comparar datetimes ignorando tzinfo

def _naive(dt: datetime) -> datetime:
    """Devuelve el datetime sin tzinfo (para comparar slots naive con start aware)."""
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

@router.post("/reservations", response_model=ActionResult)
def create_reservation(
    payload: ReservationIn,
    session: Session = Depends(get_session),
    _=Depends(require_api_key),
):
    """
    Crea una reserva persistente y la sincroniza con Google Calendar.
    Valida horario/solapes y ajusta la hora de fin a la duración del servicio.
    """
    logger.info(
        "Create reservation: service=%s pro=%s start=%s",
        payload.service_id, payload.professional_id, payload.start.isoformat()
    )

    if payload.service_id not in SERVICE_BY_ID:
        raise HTTPException(status_code=404, detail="service_id no existe")
    if payload.professional_id not in PRO_BY_ID:
        raise HTTPException(status_code=404, detail="professional_id no existe")

    # Normaliza TZ y valida rango
    start = payload.start
    if start.tzinfo is None:
        start = start.replace(tzinfo=TZ)
    try:
        validate_target_dt(start)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    service = SERVICE_BY_ID[payload.service_id]
    end = start + timedelta(minutes=service.duration_min)

    avail = find_available_slots(session, payload.service_id, start.date(), payload.professional_id)
    avail_naive = [_naive(dt) for dt in avail]
    if _naive(start) not in avail_naive:
        raise HTTPException(status_code=400, detail="Ese inicio no está disponible (horario o solapado). Consulta /slots.")

    res_id = str(uuid.uuid4())
    cal_id = get_calendar_for_professional(payload.professional_id)

    # Calendar primero; si DB falla, rollback del evento
    try:
        gcal_event = create_gcal_reservation(
            Reservation(
                id=res_id,
                service_id=payload.service_id,
                professional_id=payload.professional_id,
                start=start,
                end=end
            ),
            calendar_id=cal_id
        )
        gcal_id = gcal_event.get("id")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error en Google Calendar: {e}")

    try:
        row = ReservationDB(
            id=res_id,
            service_id=payload.service_id,
            professional_id=payload.professional_id,
            start=start,
            end=end,
            google_event_id=gcal_id,
            google_calendar_id=cal_id,
        )
        session.add(row)
        session.commit()
    except Exception as e:
        # rollback en Calendar
        try:
            if gcal_id:
                delete_gcal_reservation(gcal_id, cal_id)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"No se pudo guardar la reserva: {e}")

    logger.info(
        "Reservation created: id=%s gcal_event=%s calendar=%s start=%s end=%s",
        res_id, gcal_id, cal_id, start.isoformat(), end.isoformat()
    )
    return ActionResult(ok=True, message=f"Reserva creada y sincronizada. ID: {res_id}, Evento: {gcal_id}")

