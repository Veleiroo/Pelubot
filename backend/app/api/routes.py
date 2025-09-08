"""
Rutas y endpoints de la API (estructura nueva).
"""
from __future__ import annotations
from datetime import datetime, time, timedelta
import os
import uuid
import logging

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlmodel import Session, select

from app.data import SERVICES, PROS, SERVICE_BY_ID, PRO_BY_ID
from app.models import (
    SlotsQuery, SlotsOut,
    Reservation, CancelReservationIn, ActionResult,
    RescheduleIn, RescheduleOut, ReservationIn,
    ReservationDB,
    DaysAvailabilityIn, DaysAvailabilityOut,
)
from app.services.logic import (
    find_available_slots,
    find_reservation, cancel_reservation,
    apply_reschedule,
    create_gcal_reservation,
    patch_gcal_reservation,
    delete_gcal_reservation,
    get_calendar_for_professional,
    sync_from_gcal_range,
    reconcile_db_to_gcal_range,
    detect_conflicts_range,
)
from app.db import get_session, engine
from app.utils.date import validate_target_dt, TZ, now_tz, MAX_AHEAD_DAYS
from datetime import timezone as _utc_tz

logger = logging.getLogger("pelubot.api")

API_KEY = os.getenv("API_KEY", "changeme")
ALLOW_LOCAL_NO_AUTH = os.getenv("ALLOW_LOCAL_NO_AUTH", "false").lower() in ("1","true","yes","y","si","sí")

def require_api_key(request: Request):
    client_host = getattr(request.client, "host", None)
    if ALLOW_LOCAL_NO_AUTH and client_host in ("127.0.0.1", "localhost"):
        return
    key = request.headers.get("X-API-Key") or ""
    auth = request.headers.get("Authorization") or ""
    if not key and auth:
        parts = auth.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            key = parts[1].strip()
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

router = APIRouter()

GCAL_CALENDAR_ID = os.getenv("GCAL_CALENDAR_ID", os.getenv("GCAL_TEST_CALENDAR_ID", "pelubot.test@gmail.com"))

@router.get("/health")
def health():
    return {"ok": True}

@router.get("/ready", tags=["monitor"])
def readiness():
    status = {"db": "ok", "gcal": "ok"}
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception as e:
        status["db"] = f"error: {e}"
    try:
        # Cliente de Google Calendar: integración nueva
        from app.integrations.google_calendar import build_calendar
        _ = build_calendar()
    except Exception as e:
        status["gcal"] = f"error: {e}"
    ok = all(v == "ok" for v in status.values())
    return {"ok": ok, **status}

@router.get("/")
def home():
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

@router.get("/services")
def list_services():
    return SERVICES

@router.get("/professionals")
def list_professionals():
    return PROS

@router.get("/reservations")
def list_reservations(session: Session = Depends(get_session)):
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

@router.post("/cancel_reservation", response_model=ActionResult)
def cancel_reservation_post(payload: CancelReservationIn, session: Session = Depends(get_session), _=Depends(require_api_key)):
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
def cancel_reservation_delete(reservation_id: str, session: Session = Depends(get_session), _=Depends(require_api_key)):
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

@router.post("/reschedule", response_model=RescheduleOut)
def reschedule_post(payload: RescheduleIn, session: Session = Depends(get_session), _=Depends(require_api_key)):
    logger.info("Reschedule requested: id=%s new_date=%s new_time=%s new_pro=%s", payload.reservation_id, payload.new_date, payload.new_time, payload.professional_id)
    r_prev = find_reservation(session, payload.reservation_id)
    if not r_prev:
        raise HTTPException(status_code=404, detail="La reserva no existe")
    if payload.new_start:
        try:
            new_start = datetime.fromisoformat(str(payload.new_start).replace("Z", "+00:00"))
            if new_start.tzinfo is None:
                new_start = new_start.replace(tzinfo=TZ)
            validate_target_dt(new_start)
        except ValueError:
            raise HTTPException(status_code=400, detail="new_start inválido (ISO 8601 requerido).")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif payload.new_date and payload.new_time:
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
    message_out = msg if (isinstance(msg, str) and "Reprogramada" in msg) else f"Reprogramada: {msg}"
    if r.google_event_id:
        try:
            new_cal = get_calendar_for_professional(r.professional_id)
            if old_cal and old_cal != new_cal:
                delete_gcal_reservation(r.google_event_id, old_cal)
                gnew = create_gcal_reservation(Reservation(id=r.id, service_id=r.service_id, professional_id=r.professional_id, start=r.start, end=r.end, google_event_id=r.google_event_id, google_calendar_id=new_cal), calendar_id=new_cal)
                r.google_event_id = gnew.get("id"); r.google_calendar_id = new_cal
            else:
                patch_gcal_reservation(r.google_event_id, r.start, r.end, old_cal or new_cal)
                r.google_calendar_id = old_cal or new_cal
            session.add(r); session.commit(); session.refresh(r)
        except Exception as e:
            r.start, r.end, r.professional_id, r.google_calendar_id = old_start, old_end, old_pro, old_cal
            session.add(r); session.commit()
            raise HTTPException(status_code=502, detail=f"No se pudo reprogramar en Google Calendar: {e}")
    logger.info("Reservation rescheduled: id=%s start=%s end=%s pro=%s", r.id, r.start.isoformat(), r.end.isoformat(), r.professional_id)
    return RescheduleOut(ok=True, message=message_out, reservation_id=r.id, start=r.start.isoformat(), end=r.end.isoformat())

@router.post("/reservations/reschedule", response_model=RescheduleOut)
def reschedule_post_alias(payload: RescheduleIn, session: Session = Depends(get_session), _=Depends(require_api_key)):
    return reschedule_post(payload, session, _)

@router.post("/slots", response_model=SlotsOut)
def get_slots(q: SlotsQuery, session: Session = Depends(get_session)):
    logger.info("Slots query: service=%s date=%s pro=%s", q.service_id, q.date_str, q.professional_id)
    try:
        d = datetime.strptime(q.date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="date_str debe ser YYYY-MM-DD")
    # Validación específica para /slots: permitimos el día de hoy aunque ya haya pasado 00:00,
    # pero seguimos limitando a no más de ~6 meses vista.
    today = now_tz().date()
    if d < today:
        raise HTTPException(status_code=400, detail="La fecha está en el pasado.")
    if d > today + timedelta(days=MAX_AHEAD_DAYS):
        raise HTTPException(status_code=400, detail="La fecha excede el límite de 6 meses.")
    if q.service_id not in SERVICE_BY_ID:
        raise HTTPException(status_code=404, detail="service_id no existe")
    if q.professional_id and q.professional_id not in PRO_BY_ID:
        raise HTTPException(status_code=404, detail="professional_id no existe")
    avail = find_available_slots(session, q.service_id, d, q.professional_id, use_gcal_busy_override=q.use_gcal)
    return SlotsOut(service_id=q.service_id, date=d, professional_id=q.professional_id, slots=[dt.isoformat() for dt in avail])


@router.post("/slots/days", response_model=DaysAvailabilityOut)
def get_days_availability(body: DaysAvailabilityIn, session: Session = Depends(get_session)):
    if body.service_id not in SERVICE_BY_ID:
        raise HTTPException(status_code=404, detail="service_id no existe")
    if body.professional_id and body.professional_id not in PRO_BY_ID:
        raise HTTPException(status_code=404, detail="professional_id no existe")
    if body.end < body.start:
        raise HTTPException(status_code=400, detail="Rango inválido")
    # Limitar rango para evitar abusos
    if (body.end - body.start).days > 62:
        raise HTTPException(status_code=400, detail="Rango demasiado grande (máx. 62 días)")
    today = now_tz().date()
    available_days: list[str] = []
    d = body.start
    while d <= body.end:
        if d >= today and d <= today + timedelta(days=MAX_AHEAD_DAYS):
            slots = find_available_slots(session, body.service_id, d, body.professional_id, use_gcal_busy_override=body.use_gcal)
            if slots:
                available_days.append(d.isoformat())
        d += timedelta(days=1)
    return DaysAvailabilityOut(service_id=body.service_id, start=body.start, end=body.end, professional_id=body.professional_id, available_days=available_days)

def _naive(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

@router.post("/reservations", response_model=ActionResult)
def create_reservation(payload: ReservationIn, session: Session = Depends(get_session), _=Depends(require_api_key)):
    logger.info("Create reservation: service=%s pro=%s start=%s", payload.service_id, payload.professional_id, payload.start.isoformat())
    if payload.service_id not in SERVICE_BY_ID:
        raise HTTPException(status_code=404, detail="service_id no existe")
    if payload.professional_id not in PRO_BY_ID:
        raise HTTPException(status_code=404, detail="professional_id no existe")
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
    try:
        gcal_event = create_gcal_reservation(Reservation(id=res_id, service_id=payload.service_id, professional_id=payload.professional_id, start=start, end=end), calendar_id=cal_id)
        gcal_id = gcal_event.get("id")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error en Google Calendar: {e}")
    try:
        row = ReservationDB(id=res_id, service_id=payload.service_id, professional_id=payload.professional_id, start=start, end=end, google_event_id=gcal_id, google_calendar_id=cal_id)
        session.add(row); session.commit()
    except Exception as e:
        try:
            if gcal_id:
                delete_gcal_reservation(gcal_id, cal_id)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"No se pudo guardar la reserva: {e}")
    logger.info("Reservation created: id=%s gcal_event=%s calendar=%s start=%s end=%s", res_id, gcal_id, cal_id, start.isoformat(), end.isoformat())
    return ActionResult(ok=True, message=f"Reserva creada y sincronizada. ID: {res_id}, Evento: {gcal_id}")

# Admin
from pydantic import BaseModel

class AdminSyncIn(BaseModel):
    mode: str | None = None
    start: str | None = None
    end: str | None = None
    days: int | None = None
    by_professional: bool | None = True
    calendar_id: str | None = None
    professional_id: str | None = None
    default_service: str | None = None

@router.post("/admin/sync")
def admin_sync(body: AdminSyncIn | None = None, session: Session = Depends(get_session), _=Depends(require_api_key)):
    from datetime import date, timedelta
    body = body or AdminSyncIn()
    mode = (body.mode or "import").lower()
    start = date.fromisoformat(body.start) if body.start else date.today()
    if body.end:
        end = date.fromisoformat(body.end)
    else:
        days = body.days if body.days and body.days > 0 else 7
        end = start + timedelta(days=max(0, days - 1))
    by_prof = True if body.by_professional is None else bool(body.by_professional)
    results: dict[str, dict] = {}
    if mode in ("import", "both"):
        results["import"] = sync_from_gcal_range(session, start, end, default_service=body.default_service or "corte", by_professional=by_prof, calendar_id=body.calendar_id, professional_id=body.professional_id)
    if mode in ("push", "both"):
        results["push"] = reconcile_db_to_gcal_range(session, start, end, by_professional=by_prof, calendar_id=body.calendar_id, professional_id=body.professional_id)
    return {"ok": True, "mode": mode, "range": (start.isoformat(), end.isoformat()), "results": results}

class AdminConflictsIn(BaseModel):
    start: str | None = None
    end: str | None = None
    days: int | None = None
    by_professional: bool | None = True
    calendar_id: str | None = None
    professional_id: str | None = None

@router.post("/admin/conflicts")
def admin_conflicts(body: AdminConflictsIn | None = None, session: Session = Depends(get_session), _=Depends(require_api_key)):
    from datetime import date, timedelta
    body = body or AdminConflictsIn()
    start = date.fromisoformat(body.start) if body.start else date.today()
    if body.end:
        end = date.fromisoformat(body.end)
    else:
        days = body.days if body.days and body.days > 0 else 7
        end = start + timedelta(days=max(0, days - 1))
    by_prof = True if body.by_professional is None else bool(body.by_professional)
    summary = detect_conflicts_range(session, start, end, by_professional=by_prof, calendar_id=body.calendar_id, professional_id=body.professional_id)
    return {"ok": bool(summary.get("ok")), "range": (start.isoformat(), end.isoformat()), **summary}

class AdminClearCalendarsIn(BaseModel):
    by_professional: bool | None = True
    calendar_id: str | None = None
    calendar_ids: list[str] | None = None
    start: str | None = None
    end: str | None = None
    only_pelubot: bool | None = False
    dry_run: bool | None = True
    confirm: str | None = None

from app.integrations.google_calendar import build_calendar, clear_calendar

@router.post("/admin/clear_calendars")
def admin_clear_calendars(body: AdminClearCalendarsIn | None = None, _=Depends(require_api_key)):
    from app.data import PRO_CALENDAR
    body = body or AdminClearCalendarsIn()
    if not (body.dry_run or (body.confirm and body.confirm.upper() == "DELETE")):
        return {"ok": False, "error": "Confirmación requerida: confirm='DELETE' o dry_run=true"}
    cals: list[str] = []
    if body.calendar_ids:
        cals.extend([c for c in body.calendar_ids if c])
    if body.calendar_id:
        cals.append(body.calendar_id)
    if body.by_professional or not cals:
        cals.extend([v for v in PRO_CALENDAR.values() if v])
    cals = sorted(set(cals))
    if not cals:
        return {"ok": False, "error": "No hay calendarios destino"}
    tmin = f"{body.start}T00:00:00" if body.start else None
    tmax = f"{body.end}T23:59:59" if body.end else None
    try:
        svc = build_calendar()
    except Exception as e:
        return {"ok": False, "error": f"gcal client: {e}"}
    results = {}; total_deleted = total_listed = total_skipped = 0
    for cal in cals:
        res = clear_calendar(svc, cal, time_min=tmin, time_max=tmax, only_pelubot=bool(body.only_pelubot), dry_run=bool(body.dry_run))
        results[cal] = res
        total_deleted += res.get("deleted", 0); total_listed += res.get("total_listed", 0); total_skipped += res.get("skipped", 0)
    return {"ok": True, "dry_run": bool(body.dry_run), "only_pelubot": bool(body.only_pelubot), "calendars": cals, "range": (body.start, body.end), "totals": {"listed": total_listed, "deleted": total_deleted, "skipped": total_skipped}, "results": results}
