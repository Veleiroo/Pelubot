from __future__ import annotations
from typing import Optional, List, Tuple
from datetime import datetime, date, time, timedelta
import os
from sqlmodel import Session, select
from models import Service, RescheduleIn, Reservation, ReservationDB
from data import SERVICE_BY_ID, PROS, PRO_BY_ID, WEEKLY_SCHEDULE, PRO_CALENDAR, PRO_USE_GCAL_BUSY
from google_calendar import build_calendar, freebusy, create_event, patch_event, delete_event, iso_datetime
from zoneinfo import ZoneInfo
from datetime import timezone as _utc_tz

# ---------------------------------------------
# Lógica principal de negocio con persistencia
# ---------------------------------------------

USE_GCAL_BUSY = os.getenv("USE_GCAL_BUSY", "true").lower() in ("1", "true", "yes", "y", "si", "sí")
DEFAULT_CALENDAR_ID = os.getenv("GCAL_CALENDAR_ID", os.getenv("GCAL_TEST_CALENDAR_ID", "pelubot.test@gmail.com"))

# --- Normalización de zona horaria para comparar datetimes ---
TZ = os.getenv("TZ", "Europe/Madrid")

def _to_naive_local(dt: datetime) -> datetime:
    """
    Si 'dt' viene con tzinfo (aware), conviértelo a la TZ local y
    quita tzinfo para compararlo con datetimes naive locales.
    Si ya es naive, devuélvelo tal cual.
    """
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(ZoneInfo(TZ)).replace(tzinfo=None)

def get_calendar_for_professional(pro_id: str) -> str:
    """
    Devuelve el calendar en el que debe reservar este profesional.
    Si no hay asignado, usa el calendar general (entorno).
    """
    return PRO_CALENDAR.get(pro_id) or DEFAULT_CALENDAR_ID

def parse_date(s: str) -> Optional[date]:
    """
    Acepta 'YYYY-MM-DD' o 'DD/MM' (asumiendo año actual).
    Devuelve date o None si no parsea.
    """
    s = (s or "").strip()
    if not s:
        return None
    try:
        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        pass
    try:
        if len(s) in (4, 5) and "/" in s:
            d = datetime.strptime(s, "%d/%m").date()
            return d.replace(year=datetime.now().year)
    except Exception:
        pass
    return None

def parse_time(s: str) -> Optional[time]:
    """
    Acepta 'HH:MM' (24h). Devuelve time o None.
    """
    s = (s or "").strip()
    try:
        return datetime.strptime(s, "%H:%M").time()
    except Exception:
        return None

# --------------------------
# Consultas a la base de datos
# --------------------------
def _reservations_for_prof_on_date(session: Session, pro_id: str, on_date: date) -> List[ReservationDB]:
    """
    Devuelve reservas del profesional en esa fecha (rango 00:00-23:59).
    """
    day_start = datetime.combine(on_date, time(0, 0))
    day_end = datetime.combine(on_date, time(23, 59, 59))
    stmt = (
        select(ReservationDB)
        .where(ReservationDB.professional_id == pro_id)
        .where(ReservationDB.start < day_end)
        .where(ReservationDB.end > day_start)
    )
    return list(session.exec(stmt))

def find_reservation(session: Session, reservation_id: str) -> Optional[ReservationDB]:
    """
    Busca una reserva por su identificador.
    """
    return session.get(ReservationDB, reservation_id)

def cancel_reservation(session: Session, reservation_id: str) -> bool:
    """
    Elimina una reserva por id. Devuelve True si se eliminó.
    """
    r = session.get(ReservationDB, reservation_id)
    if not r:
        return False
    session.delete(r)
    session.commit()
    return True


# --------------------------
# Slots y validaciones
# --------------------------
def find_available_slots(
    session: Session,
    service_id: str,
    on_date: date,
    professional_id: Optional[str] = None,
    step_min: int = 15,
    use_gcal_busy_override: Optional[bool] = None,
) -> List[datetime]:
    """
    Busca los horarios disponibles para un servicio y profesional en una fecha dada.
    Considera el horario de la peluquería y reservas persistidas.
    Si USE_GCAL_BUSY=true, también excluye intervalos ocupados por Google Calendar por profesional.
    Se puede forzar por petición con use_gcal_busy_override.
    """
    service: Service = SERVICE_BY_ID[service_id]
    day_ranges = WEEKLY_SCHEDULE.get(on_date.weekday(), [])
    if not day_ranges:
        return []

    pro_ids = [professional_id] if professional_id else [p.id for p in PROS if service_id in p.services]

    starts: List[datetime] = []
    for start_t, end_t in day_ranges:
        cursor = datetime.combine(on_date, start_t)
        end_range = datetime.combine(on_date, end_t)
        while cursor + timedelta(minutes=service.duration_min) <= end_range:
            starts.append(cursor)
            cursor += timedelta(minutes=step_min)

    # Determinar por profesional si aplicar busy de GCAL
    def pro_uses_gcal(pid: str) -> bool:
        if use_gcal_busy_override is not None:
            return bool(use_gcal_busy_override)
        return PRO_USE_GCAL_BUSY.get(pid, USE_GCAL_BUSY)

    # Busy de Calendar por profesional (tolerante a fallos)
    gcal_busy_map: dict[str, List[Tuple[datetime, datetime]]] = {}
    pros_needing_gcal = [pid for pid in pro_ids if pro_uses_gcal(pid)]
    if pros_needing_gcal:
        svc = None
        try:
            svc = build_calendar()
        except Exception:
            svc = None
        if svc:
            day_start = datetime.combine(on_date, time(0, 0))
            day_end = datetime.combine(on_date, time(23, 59))
            for pid in pros_needing_gcal:
                try:
                    cal_id = get_calendar_for_professional(pid)
                    busy = freebusy(svc, cal_id, iso_datetime(day_start), iso_datetime(day_end))
                    intervals: List[Tuple[datetime, datetime]] = []
                    for b in busy:
                        try:
                            bs = datetime.fromisoformat(b["start"].replace("Z", "+00:00"))
                            be = datetime.fromisoformat(b["end"].replace("Z", "+00:00"))
                            bs = _to_naive_local(bs)
                            be = _to_naive_local(be)
                            intervals.append((bs, be))
                        except Exception:
                            continue
                    gcal_busy_map[pid] = intervals
                except Exception:
                    gcal_busy_map[pid] = []

    def overlaps_local(pro_id: str, start_dt: datetime, end_dt: datetime) -> bool:
        for r in _reservations_for_prof_on_date(session, pro_id, start_dt.date()):
            if not (end_dt <= r.start or start_dt >= r.end):
                return True
        return False

    def overlaps_intervals(start_dt: datetime, end_dt: datetime, intervals: List[Tuple[datetime, datetime]]) -> bool:
        for s, e in intervals:
            if not (end_dt <= s or start_dt >= e):
                return True
        return False

    free: List[datetime] = []
    for start_dt in starts:
        end_dt = start_dt + timedelta(minutes=service.duration_min)
        slot_ok = False
        for pro_id in pro_ids:
            if overlaps_local(pro_id, start_dt, end_dt):
                continue
            intervals = gcal_busy_map.get(pro_id, []) if pro_uses_gcal(pro_id) else []
            if overlaps_intervals(start_dt, end_dt, intervals):
                continue
            slot_ok = True
            break
        if slot_ok:
            free.append(start_dt)
    return free


def _fits_in_schedule(start_dt: datetime, duration_min: int) -> bool:
    """Verifica si un horario encaja en el rango de atención del día."""
    day_ranges = WEEKLY_SCHEDULE.get(start_dt.weekday(), [])
    if not day_ranges:
        return False
    end_dt = start_dt + timedelta(minutes=duration_min)
    for start_t, end_t in day_ranges:
        start_range = datetime.combine(start_dt.date(), start_t)
        end_range = datetime.combine(start_dt.date(), end_t)
        if start_dt >= start_range and end_dt <= end_range:
            return True
    return False


def apply_reschedule(session: Session, payload: RescheduleIn) -> Tuple[bool, str, Optional[ReservationDB]]:
    """
    Aplica la reprogramación de una reserva, validando horarios y profesional (persistente).
    """
    r = find_reservation(session, payload.reservation_id)
    if not r:
        return False, "La reserva no existe.", None

    service = SERVICE_BY_ID[r.service_id]

    if payload.new_date:
        try:
            new_date = datetime.strptime(payload.new_date, "%Y-%m-%d").date()
        except Exception:
            return False, "new_date inválida. Usa YYYY-MM-DD.", None
    else:
        new_date = r.start.date()

    if payload.new_time:
        try:
            new_time = datetime.strptime(payload.new_time, "%H:%M").time()
        except Exception:
            return False, "new_time inválida. Usa HH:MM (24h).", None
    else:
        new_time = r.start.time()

    new_pro = payload.professional_id or r.professional_id
    if new_pro not in PRO_BY_ID:
        return False, "professional_id no existe.", None

    start_dt = datetime.combine(new_date, new_time)
    end_dt = start_dt + timedelta(minutes=service.duration_min)

    if not _fits_in_schedule(start_dt, service.duration_min):
        return False, "La nueva hora no encaja en el horario.", None

    # solapes locales
    for x in _reservations_for_prof_on_date(session, new_pro, new_date):
        if x.id == r.id:
            continue
        if not (end_dt <= x.start or start_dt >= x.end):
            return False, f"El profesional {PRO_BY_ID[new_pro].name} ya tiene esa hora ocupada.", None

    # aplicar en memoria y persistir
    r.professional_id = new_pro
    r.start = start_dt
    r.end = end_dt
    r.updated_at = datetime.now(_utc_tz.utc)
    session.add(r)
    session.commit()
    session.refresh(r)
    return True, "Reserva reprogramada.", r

# --- Integración con Google Calendar ---
def find_gcal_busy_slots(calendar_id: str, on_date: date, tz: str = "Europe/Madrid") -> List[dict]:
    """
    Consulta los intervalos ocupados en Google Calendar para una fecha dada.
    Devuelve lista de rangos {"start": ..., "end": ...}
    """
    service = build_calendar()
    start_iso = iso_datetime(datetime.combine(on_date, time(0, 0)), tz)
    end_iso = iso_datetime(datetime.combine(on_date, time(23, 59)), tz)
    return freebusy(service, calendar_id, start_iso, end_iso, tz)

def create_gcal_reservation(reservation: Reservation, calendar_id: str = None, tz: str = "Europe/Madrid") -> dict:
    """
    Crea un evento en Google Calendar a partir de una reserva local. Devuelve el evento creado.
    """
    service = build_calendar()
    if not calendar_id:
        calendar_id = get_calendar_for_professional(reservation.professional_id)
    return create_event(
        service,
        calendar_id,
        reservation.start,
        reservation.end,
        summary=f"Reserva: {reservation.service_id} - {reservation.professional_id}",
        private_props={"reservation_id": reservation.id, "professional_id": reservation.professional_id},
        tz=tz
    )

def patch_gcal_reservation(event_id: str, new_start: datetime, new_end: datetime, calendar_id: str, tz: str = "Europe/Madrid") -> dict:
    """
    Modifica un evento en Google Calendar (reprograma la reserva). Devuelve el evento actualizado.
    """
    service = build_calendar()
    return patch_event(service, calendar_id, event_id, new_start, new_end, tz)

def delete_gcal_reservation(event_id: str, calendar_id: str) -> None:
    """
    Elimina un evento de Google Calendar asociado a una reserva.
    """
    service = build_calendar()
    delete_event(service, calendar_id, event_id)

# Añadimos list_events_range para sincronización
from google_calendar import list_events_range

# --- Sincronización entrante desde Google Calendar ---
def _parse_gcal_dt(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        # si llega como fecha sin hora
        return datetime.fromisoformat(s + "T00:00:00+00:00")

def _detect_service_from_summary(summary: str, default_sid: str) -> str:
    s = (summary or "").lower()
    if "tinte" in s:
        return "tinte"
    if "barba" in s:
        return "barba"
    if "corte" in s:
        return "corte"
    return default_sid

def sync_from_gcal_range(
    session: Session,
    start_date: date,
    end_date: date,
    default_service: str = "corte",
    by_professional: bool = True,
    calendar_id: str | None = None,
    professional_id: str | None = None,
    tz: str = os.getenv("TZ", "Europe/Madrid"),
) -> dict:
    """
    Importa eventos de Google Calendar a la base local (upsert) en el rango [start_date, end_date].
    - Si by_professional=True, usa data.PRO_CALENDAR.
    - Si False, requiere calendar_id (y opcional professional_id) explícitos.

    Retorna: {inserted: int, updated: int, calendars: int}
    """
    from data import PRO_CALENDAR  # import local para evitar ciclos durante tests
    svc = None
    try:
        svc = build_calendar()
    except Exception:
        # si no hay credenciales, no hacemos nada
        return {"inserted": 0, "updated": 0, "calendars": 0, "ok": False, "error": "gcal client"}

    # construir lista de (calendar_id, pro_id)
    pairs: list[tuple[str, str | None]] = []
    if by_professional:
        for pro_id, cal in PRO_CALENDAR.items():
            pairs.append((cal, pro_id))
    else:
        if not calendar_id:
            return {"inserted": 0, "updated": 0, "calendars": 0, "ok": False, "error": "calendar_id requerido"}
        pairs.append((calendar_id, professional_id))

    total_ins = total_upd = 0
    for cal_id, pro_id in pairs:
        d = start_date
        while d <= end_date:
            start_iso = f"{d.isoformat()}T00:00:00"
            end_iso = f"{d.isoformat()}T23:59:59"
            try:
                items = list_events_range(svc, cal_id, start_iso, end_iso, tz)
            except Exception:
                items = []
            for it in items:
                start_v = (it.get("start") or {}).get("dateTime") or (it.get("start") or {}).get("date")
                end_v = (it.get("end") or {}).get("dateTime") or (it.get("end") or {}).get("date")
                if not start_v or not end_v:
                    continue
                start_dt = _parse_gcal_dt(start_v)
                end_dt = _parse_gcal_dt(end_v)
                priv = (it.get("extendedProperties") or {}).get("private") or {}
                rid = priv.get("reservation_id") or f"gcal:{it.get('id')}"
                srv_id = priv.get("service_id") or _detect_service_from_summary(it.get("summary"), default_service)
                pro = priv.get("professional_id") or pro_id
                if not pro:
                    continue
                r = session.get(ReservationDB, rid)
                if r is None:
                    r = ReservationDB(
                        id=rid,
                        service_id=srv_id,
                        professional_id=str(pro),
                        start=start_dt,
                        end=end_dt,
                        google_event_id=it.get("id"),
                        google_calendar_id=cal_id,
                    )
                    session.add(r)
                    total_ins += 1
                else:
                    changed = False
                    if r.start != start_dt:
                        r.start = start_dt; changed = True
                    if r.end != end_dt:
                        r.end = end_dt; changed = True
                    if r.professional_id != pro:
                        r.professional_id = str(pro); changed = True
                    if r.service_id != srv_id:
                        r.service_id = srv_id; changed = True
                    if r.google_event_id != it.get("id"):
                        r.google_event_id = it.get("id"); changed = True
                    if r.google_calendar_id != cal_id:
                        r.google_calendar_id = cal_id; changed = True
                    if changed:
                        session.add(r)
                        total_upd += 1
            d += timedelta(days=1)
        session.commit()
    return {"ok": True, "inserted": total_ins, "updated": total_upd, "calendars": len(pairs)}
