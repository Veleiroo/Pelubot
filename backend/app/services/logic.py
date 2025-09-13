from __future__ import annotations
from typing import Optional, List, Tuple
from datetime import datetime, date, time, timedelta
import os
from sqlmodel import Session, select
from app.models import Service, RescheduleIn, Reservation, ReservationDB
from app.data import SERVICE_BY_ID, PROS, PRO_BY_ID, WEEKLY_SCHEDULE, PRO_CALENDAR, PRO_USE_GCAL_BUSY
from app.integrations.google_calendar import build_calendar, freebusy, freebusy_multi, create_event, patch_event, delete_event, iso_datetime, list_events_range
from zoneinfo import ZoneInfo
from datetime import timezone as _utc_tz

# ---------------------------------------------
# Lógica de negocio con persistencia
# ---------------------------------------------

USE_GCAL_BUSY = os.getenv("USE_GCAL_BUSY", "true").lower() in ("1", "true", "yes", "y", "si", "sí")
DEFAULT_CALENDAR_ID = os.getenv("GCAL_CALENDAR_ID", os.getenv("GCAL_TEST_CALENDAR_ID", "pelubot.test@gmail.com"))

TZ = os.getenv("TZ", "Europe/Madrid")

def _to_naive_local(dt: datetime) -> datetime:
    """Convierte a la TZ local y devuelve datetime naive para comparaciones internas."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(ZoneInfo(TZ)).replace(tzinfo=None)

def get_calendar_for_professional(pro_id: str) -> str:
    """Calendar destino para el profesional; fallback al calendar general."""
    return PRO_CALENDAR.get(pro_id) or DEFAULT_CALENDAR_ID

def parse_date(s: str) -> Optional[date]:
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
    s = (s or "").strip()
    try:
        return datetime.strptime(s, "%H:%M").time()
    except Exception:
        return None

def _reservations_for_prof_on_date(session: Session, pro_id: str, on_date: date) -> List[ReservationDB]:
    """Reservas del profesional que solapan el día."""
    day_start = datetime.combine(on_date, time(0, 0))
    day_end = datetime.combine(on_date, time(23, 59, 59))
    stmt = select(ReservationDB).where(ReservationDB.professional_id == pro_id, ReservationDB.start < day_end, ReservationDB.end > day_start)
    return list(session.exec(stmt))

def find_reservation(session: Session, reservation_id: str) -> Optional[ReservationDB]:
    return session.get(ReservationDB, reservation_id)

def cancel_reservation(session: Session, reservation_id: str) -> bool:
    r = session.get(ReservationDB, reservation_id)
    if not r:
        return False
    session.delete(r)
    session.commit()
    return True

def find_available_slots(session: Session, service_id: str, on_date: date, professional_id: Optional[str] = None, step_min: int = 15, use_gcal_busy_override: Optional[bool] = None) -> List[datetime]:
    """Calcula huecos disponibles considerando agenda, reservas locales y opcionalmente busy de GCal."""
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

    def pro_uses_gcal(pid: str) -> bool:
        if use_gcal_busy_override is not None:
            return bool(use_gcal_busy_override)
        return PRO_USE_GCAL_BUSY.get(pid, USE_GCAL_BUSY)

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
            # Consulta freebusy en una sola llamada para todos los calendarios implicados
            cal_map: dict[str, str] = {pid: get_calendar_for_professional(pid) for pid in pros_needing_gcal}
            cal_ids = list({cid for cid in cal_map.values() if cid})
            try:
                busy_map = freebusy_multi(svc, cal_ids, iso_datetime(day_start), iso_datetime(day_end)) if cal_ids else {}
            except Exception:
                busy_map = {}
            for pid, cid in cal_map.items():
                try:
                    entries = busy_map.get(cid, [])
                except Exception:
                    entries = []
                intervals: List[Tuple[datetime, datetime]] = []
                for b in entries:
                    try:
                        bs = _to_naive_local(datetime.fromisoformat((b.get("start") or "").replace("Z", "+00:00")))
                        be = _to_naive_local(datetime.fromisoformat((b.get("end") or "").replace("Z", "+00:00")))
                        intervals.append((bs, be))
                    except Exception:
                        continue
                gcal_busy_map[pid] = intervals

    def overlaps_local(pro_id: str, start_dt: datetime, end_dt: datetime) -> bool:
        for r in _reservations_for_prof_on_date(session, pro_id, start_dt.date()):
            if not (end_dt <= r.start or start_dt >= r.end):
                return True
        return False

    def overlaps_intervals(start_dt: datetime, end_dt: datetime, intervals: List[Tuple[datetime, datetime]]) -> bool:
        return any(not (end_dt <= s or start_dt >= e) for s, e in intervals)

    free: List[datetime] = []
    for start_dt in starts:
        end_dt = start_dt + timedelta(minutes=service.duration_min)
        for pro_id in pro_ids:
            if overlaps_local(pro_id, start_dt, end_dt):
                continue
            intervals = gcal_busy_map.get(pro_id, []) if pro_uses_gcal(pro_id) else []
            if overlaps_intervals(start_dt, end_dt, intervals):
                continue
            free.append(start_dt)
            break
    return free

def _fits_in_schedule(start_dt: datetime, duration_min: int) -> bool:
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
    """Reprograma una reserva, validando agenda/solapes. Soporta new_start o (new_date,new_time)."""
    r = find_reservation(session, payload.reservation_id)
    if not r:
        return False, "La reserva no existe.", None
    service = SERVICE_BY_ID[r.service_id]

    new_start_dt: Optional[datetime] = None
    if getattr(payload, "new_start", None):
        try:
            new_start_dt = datetime.fromisoformat(str(payload.new_start).replace("Z", "+00:00"))
            if new_start_dt.tzinfo is None:
                new_start_dt = new_start_dt.replace(tzinfo=ZoneInfo(TZ))
        except Exception:
            return False, "new_start inválido. Usa ISO 8601.", None
    if new_start_dt is None:
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
        new_start_dt = datetime.combine(new_date, new_time)

    new_pro = payload.professional_id or r.professional_id
    if new_pro not in PRO_BY_ID:
        return False, "professional_id no existe.", None

    # Usamos naive local únicamente para comparaciones internas; en BD guardamos TZ-aware
    start_dt = _to_naive_local(new_start_dt)
    end_dt = start_dt + timedelta(minutes=service.duration_min)

    if not _fits_in_schedule(start_dt, service.duration_min):
        return False, "La nueva hora no encaja en el horario.", None

    for x in _reservations_for_prof_on_date(session, new_pro, start_dt.date()):
        if x.id == r.id:
            continue
        if not (end_dt <= x.start or start_dt >= x.end):
            return False, f"El profesional {PRO_BY_ID[new_pro].name} ya tiene esa hora ocupada.", None

    r.professional_id = new_pro
    # Persistimos como TZ-aware (coherente con columnas timezone=True)
    try:
        tz = ZoneInfo(TZ)
    except Exception:
        tz = None
    r.start = start_dt.replace(tzinfo=tz) if tz else start_dt
    r.end = end_dt.replace(tzinfo=tz) if tz else end_dt
    r.updated_at = datetime.now(_utc_tz.utc)
    session.add(r)
    session.commit()
    session.refresh(r)
    return True, "Reserva reprogramada.", r

def find_gcal_busy_slots(calendar_id: str, on_date: date, tz: str = "Europe/Madrid") -> List[dict]:
    service = build_calendar()
    start_iso = iso_datetime(datetime.combine(on_date, time(0, 0)), tz)
    end_iso = iso_datetime(datetime.combine(on_date, time(23, 59)), tz)
    return freebusy(service, calendar_id, start_iso, end_iso, tz)

def create_gcal_reservation(reservation: Reservation, calendar_id: str = None, tz: str = "Europe/Madrid") -> dict:
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
        tz=tz,
    )

def patch_gcal_reservation(event_id: str, new_start: datetime, new_end: datetime, calendar_id: str, tz: str = "Europe/Madrid") -> dict:
    service = build_calendar()
    return patch_event(service, calendar_id, event_id, new_start, new_end, tz)

def delete_gcal_reservation(event_id: str, calendar_id: str) -> None:
    service = build_calendar()
    delete_event(service, calendar_id, event_id)

def _parse_gcal_dt(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
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

def sync_from_gcal_range(session: Session, start_date: date, end_date: date, default_service: str = "corte", by_professional: bool = True, calendar_id: str | None = None, professional_id: str | None = None, tz: str = os.getenv("TZ", "Europe/Madrid")) -> dict:
    """Importa eventos de GCal a la BD (upsert) en [start_date, end_date]."""
    from app.data import PRO_CALENDAR
    try:
        svc = build_calendar()
    except Exception:
        return {"inserted": 0, "updated": 0, "calendars": 0, "ok": False, "error": "gcal client"}
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
            start_iso = f"{d.isoformat()}T00:00:00"; end_iso = f"{d.isoformat()}T23:59:59"
            try:
                items = list_events_range(svc, cal_id, start_iso, end_iso, tz)
            except Exception:
                items = []
            for it in items:
                start_v = (it.get("start") or {}).get("dateTime") or (it.get("start") or {}).get("date")
                end_v = (it.get("end") or {}).get("dateTime") or (it.get("end") or {}).get("date")
                if not start_v or not end_v:
                    continue
                start_dt = _parse_gcal_dt(start_v); end_dt = _parse_gcal_dt(end_v)
                priv = (it.get("extendedProperties") or {}).get("private") or {}
                rid = priv.get("reservation_id") or f"gcal:{it.get('id')}"
                srv_id = priv.get("service_id") or _detect_service_from_summary(it.get("summary"), default_service)
                pro = priv.get("professional_id") or pro_id
                if not pro:
                    continue
                r = session.get(ReservationDB, rid)
                if r is None:
                    r = ReservationDB(id=rid, service_id=srv_id, professional_id=str(pro), start=start_dt, end=end_dt, google_event_id=it.get("id"), google_calendar_id=cal_id)
                    session.add(r); total_ins += 1
                else:
                    changed = False
                    if r.start != start_dt: r.start = start_dt; changed = True
                    if r.end != end_dt: r.end = end_dt; changed = True
                    if r.professional_id != pro: r.professional_id = str(pro); changed = True
                    if r.service_id != srv_id: r.service_id = srv_id; changed = True
                    if r.google_event_id != it.get("id"): r.google_event_id = it.get("id"); changed = True
                    if r.google_calendar_id != cal_id: r.google_calendar_id = cal_id; changed = True
                    if changed: session.add(r); total_upd += 1
            d += timedelta(days=1)
        session.commit()
    return {"ok": True, "inserted": total_ins, "updated": total_upd, "calendars": len(pairs)}

def reconcile_db_to_gcal_range(session: Session, start_date: date, end_date: date, by_professional: bool = True, calendar_id: str | None = None, professional_id: str | None = None, tz: str = os.getenv("TZ", "Europe/Madrid")) -> dict:
    """Alinea eventos de GCal con la BD local: crea, parchea o mueve entre calendarios."""
    from app.data import PRO_CALENDAR
    try:
        svc = build_calendar()
    except Exception:
        return {"ok": False, "created": 0, "patched": 0, "calendars": 0, "error": "gcal client"}
    pairs: list[tuple[str, str | None]] = []
    if by_professional:
        for pid, cal in PRO_CALENDAR.items():
            pairs.append((cal, pid))
    else:
        if not calendar_id:
            return {"ok": False, "created": 0, "patched": 0, "calendars": 0, "error": "calendar_id requerido"}
        pairs.append((calendar_id, professional_id))
    created = patched = 0
    def _day_bounds(d: date):
        return datetime.combine(d, time(0, 0)), datetime.combine(d, time(23, 59, 59))
    for cal_id, pro_id in pairs:
        d = start_date
        while d <= end_date:
            day_start, day_end = _day_bounds(d)
            try:
                gitems = list_events_range(svc, cal_id, iso_datetime(day_start, tz), iso_datetime(day_end, tz), tz)
            except Exception:
                gitems = []
            gmap = {it.get("id"): it for it in gitems if it.get("id")}
            q = select(ReservationDB).where(ReservationDB.start < day_end, ReservationDB.end > day_start)
            if pro_id:
                q = q.where(ReservationDB.professional_id == pro_id)
            rows = list(session.exec(q))
            for r in rows:
                target_cal = get_calendar_for_professional(r.professional_id)
                if r.google_event_id and r.google_calendar_id and r.google_calendar_id != target_cal:
                    try:
                        delete_event(svc, r.google_calendar_id, r.google_event_id)
                    except Exception:
                        pass
                    ev = create_event(svc, target_cal, r.start, r.end, summary=f"Reserva: {r.service_id} - {r.professional_id}", private_props={"reservation_id": r.id, "professional_id": r.professional_id, "service_id": r.service_id}, tz=tz)
                    r.google_event_id = ev.get("id"); r.google_calendar_id = target_cal
                    session.add(r); created += 1
                    continue
                if not r.google_event_id or r.google_event_id not in gmap:
                    ev = create_event(svc, target_cal, r.start, r.end, summary=f"Reserva: {r.service_id} - {r.professional_id}", private_props={"reservation_id": r.id, "professional_id": r.professional_id, "service_id": r.service_id}, tz=tz)
                    r.google_event_id = ev.get("id"); r.google_calendar_id = target_cal
                    session.add(r); created += 1
                    continue
                it = gmap.get(r.google_event_id)
                gs = (it.get("start") or {}).get("dateTime") or (it.get("start") or {}).get("date")
                ge = (it.get("end") or {}).get("dateTime") or (it.get("end") or {}).get("date")
                if gs and ge:
                    gs_dt = _parse_gcal_dt(gs); ge_dt = _parse_gcal_dt(ge)
                    if gs_dt != r.start or ge_dt != r.end:
                        patch_event(svc, target_cal, r.google_event_id, r.start, r.end, tz); patched += 1
            d += timedelta(days=1)
        session.commit()
    return {"ok": True, "created": created, "patched": patched, "calendars": len(pairs)}

def detect_conflicts_range(session: Session, start_date: date, end_date: date, by_professional: bool = True, calendar_id: str | None = None, professional_id: str | None = None, tz: str = os.getenv("TZ", "Europe/Madrid")) -> dict:
    """Detecta inconsistencias BD ↔ GCal: faltantes, huérfanos, desajustes y solapes externos."""
    try:
        svc = build_calendar()
    except Exception as e:
        return {"ok": False, "error": f"gcal client: {e}"}
    from app.data import PRO_CALENDAR
    pairs: list[tuple[str, str | None]] = []
    if by_professional:
        for pid, cal in PRO_CALENDAR.items():
            pairs.append((cal, pid))
    else:
        if not calendar_id:
            return {"ok": False, "error": "calendar_id requerido"}
        pairs.append((calendar_id, professional_id))
    summary = {"ok": True, "calendars": len(pairs), "missing_in_gcal": 0, "orphaned_in_gcal": 0, "time_mismatch": 0, "overlaps_external": 0, "samples": {"missing_in_gcal": [], "orphaned_in_gcal": [], "time_mismatch": [], "overlaps_external": []}}
    def _add_sample(kind: str, item: dict):
        arr = summary["samples"][kind]
        if len(arr) < 10: arr.append(item)
    d = start_date
    while d <= end_date:
        day_start = datetime.combine(d, time(0, 0)); day_end = datetime.combine(d, time(23, 59, 59))
        for cal_id, pro_id in pairs:
            try:
                items = list_events_range(svc, cal_id, iso_datetime(day_start, tz), iso_datetime(day_end, tz), tz)
            except Exception:
                items = []
            gmap = {it.get("id"): it for it in items if it.get("id")}
            q = select(ReservationDB).where(ReservationDB.start < day_end, ReservationDB.end > day_start)
            if pro_id:
                q = q.where(ReservationDB.professional_id == pro_id)
            locals_rows = list(session.exec(q))
            for r in locals_rows:
                tgt_cal = get_calendar_for_professional(r.professional_id)
                if not r.google_event_id or r.google_event_id not in gmap or (r.google_calendar_id and r.google_calendar_id != tgt_cal):
                    summary["missing_in_gcal"] += 1
                    _add_sample("missing_in_gcal", {"id": r.id, "cal": tgt_cal, "start": r.start.isoformat()})
            for it in items:
                ev_id = it.get("id")
                start_v = (it.get("start") or {}).get("dateTime") or (it.get("start") or {}).get("date")
                end_v = (it.get("end") or {}).get("dateTime") or (it.get("end") or {}).get("date")
                if not start_v or not end_v:
                    continue
                sdt = _parse_gcal_dt(start_v); edt = _parse_gcal_dt(end_v)
                priv = (it.get("extendedProperties") or {}).get("private") or {}
                rid = priv.get("reservation_id")
                if rid:
                    r = session.get(ReservationDB, rid)
                    if not r:
                        summary["orphaned_in_gcal"] += 1
                        _add_sample("orphaned_in_gcal", {"event_id": ev_id, "rid": rid, "cal": cal_id})
                    else:
                        if _to_naive_local(r.start) != _to_naive_local(sdt) or _to_naive_local(r.end) != _to_naive_local(edt):
                            summary["time_mismatch"] += 1
                            _add_sample("time_mismatch", {"rid": r.id, "event_id": ev_id})
                    continue
                for r in locals_rows:
                    if r.google_event_id == ev_id:
                        continue
                    if not (edt <= r.start or sdt >= r.end):
                        summary["overlaps_external"] += 1
                        _add_sample("overlaps_external", {"event_id": ev_id, "rid": r.id})
                        break
        d += timedelta(days=1)
    return summary
