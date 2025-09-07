#!/usr/bin/env python3
"""
Google Calendar Smoke Test (standalone)
--------------------------------------
Prueba de autenticación y operaciones básicas contra Google Calendar:
- Listar calendarios
- FreeBusy (ocupado/libre)
- Crear evento de prueba
- Reprogramar (patch)
- Borrar evento

Autenticación soportada (elige una):
A) Service Account  -> export GOOGLE_SERVICE_ACCOUNT_JSON=/ruta/al/cred.json
   (Opcional Workspace) export GOOGLE_IMPERSONATE_EMAIL=usuario@tu-dominio.com
B) OAuth de Usuario -> export GOOGLE_OAUTH_JSON=/ruta/al/oauth_tokens.json

Variables recomendadas:
- GCAL_TEST_CALENDAR_ID : ID del calendario donde operar
- TZ : zona horaria (por defecto Europe/Madrid)

Instalación:
  pip install --upgrade google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2

Ejemplos:
  python prueba.py list-calendars
  python prueba.py freebusy --start "2025-09-04T09:00:00" --end "2025-09-04T18:00:00" --calendar "$GCAL_TEST_CALENDAR_ID"
  python prueba.py create --start "2025-09-05T10:00:00" --end "2025-09-05T10:30:00" --calendar "$GCAL_TEST_CALENDAR_ID" --summary "Test corte"
  python prueba.py patch --event-id "<ID>" --start "2025-09-05T11:00:00" --end "2025-09-05T11:30:00" --calendar "$GCAL_TEST_CALENDAR_ID"
  python prueba.py delete --event-id "<ID>" --calendar "$GCAL_TEST_CALENDAR_ID"
  python prueba.py sync-from-gcal --by-professional --day 2025-09-07 --default-service corte
"""
from __future__ import annotations

import os
import json
import sys
import argparse
from datetime import datetime, timedelta, date
from typing import Dict, Optional, List, Tuple
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials as SA
from google.oauth2.credentials import Credentials as UserCreds
from googleapiclient.discovery import build

# Cargar .env desde el proyecto si existe
_here = Path(__file__).resolve().parent
_root = _here.parent
load_dotenv()  # intenta desde CWD
if not os.getenv("GOOGLE_OAUTH_JSON") and (_root / ".env").exists():
    load_dotenv(_root / ".env")

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def _load_service_account() -> Optional[SA]:
    """
    Carga las credenciales de Service Account desde la variable de entorno.
    Permite formato JSON directo o ruta a archivo.
    Si se indica GOOGLE_IMPERSONATE_EMAIL, usa impersonación.
    """
    sa = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa:
        return None
    if sa.strip().startswith("{"):
        info = json.loads(sa)
    else:
        with open(sa, "r", encoding="utf-8") as f:
            info = json.load(f)
    creds = SA.from_service_account_info(info, scopes=SCOPES)
    subject = os.getenv("GOOGLE_IMPERSONATE_EMAIL")
    if subject:
        creds = creds.with_subject(subject)
    return creds

def _resolve_oauth_path(oa: str) -> Path:
    """Resuelve una ruta potencialmente relativa para GOOGLE_OAUTH_JSON de forma robusta."""
    p = Path(oa)
    if p.is_absolute() and p.exists():
        return p
    # 1) relativa al CWD
    cand = Path(os.getcwd()) / p
    if cand.exists():
        return cand
    # 2) relativa a la raíz del proyecto
    cand = _here.parent / p
    if cand.exists():
        return cand
    # 3) relativa al directorio del módulo
    cand = _here / p
    if cand.exists():
        return cand
    # 4) solo el nombre en el directorio del módulo
    cand = _here / p.name
    return cand

def _load_user_oauth() -> Optional[UserCreds]:
    """
    Carga las credenciales OAuth de usuario desde la variable de entorno.
    Permite formato JSON directo o ruta a archivo.
    Refresca el token si está expirado.
    """
    oa = os.getenv("GOOGLE_OAUTH_JSON")
    if not oa:
        # Fallback al archivo local junto al script
        fallback = _here / "oauth_tokens.json"
        if fallback.exists():
            oa = str(fallback)
        else:
            return None
    if oa.strip().startswith("{"):
        info = json.loads(oa)
    else:
        path = _resolve_oauth_path(oa)
        with open(path, "r", encoding="utf-8") as f:
            info = json.load(f)
    creds = UserCreds.from_authorized_user_info(info, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

def build_calendar():
    """
    Construye el cliente de Google Calendar usando las credenciales disponibles.
    Prioriza Service Account sobre OAuth de usuario.
    """
    sa_creds = _load_service_account()
    if sa_creds:
        return build("calendar", "v3", credentials=sa_creds)
    oa_creds = _load_user_oauth()
    if oa_creds:
        return build("calendar", "v3", credentials=oa_creds)
    raise RuntimeError("No hay credenciales. Exporta GOOGLE_SERVICE_ACCOUNT_JSON o GOOGLE_OAUTH_JSON")

def list_calendars(svc):
    """
    Lista todos los calendarios accesibles por el usuario o service account.
    """
    items = svc.calendarList().list().execute().get("items", [])
    for it in items:
        print(f"- {it.get('summary')} :: {it.get('id')} (primary={it.get('primary', False)})")

def freebusy(svc, calendar_id: str, time_min: str, time_max: str, tz: str):
    """
    Consulta los intervalos ocupados (busy) en el calendario indicado entre dos fechas.
    """
    body = {"timeMin": time_min, "timeMax": time_max, "timeZone": tz, "items": [{"id": calendar_id}]}
    try:
        fb = svc.freebusy().query(body=body).execute()
        busy = fb.get("calendars", {}).get(calendar_id, {}).get("busy", [])
        print(json.dumps(busy, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"ERROR consultando freebusy: {e}", file=sys.stderr)

def create_event(svc, calendar_id: str, start_iso: str, end_iso: str, summary: str, tz: str, private: Dict[str, str]):
    """
    Crea un evento en el calendario indicado.
    Permite añadir propiedades privadas (meta).
    """
    body = {
        "summary": summary,
        "start": {"dateTime": start_iso, "timeZone": tz},
        "end": {"dateTime": end_iso, "timeZone": tz},
        "extendedProperties": {"private": private},
    }
    try:
        evt = svc.events().insert(calendarId=calendar_id, body=body).execute()
        print(json.dumps({"id": evt["id"], "htmlLink": evt.get("htmlLink")}, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"ERROR creando evento: {e}", file=sys.stderr)

def patch_event(svc, calendar_id: str, event_id: str, start_iso: str, end_iso: str, tz: str):
    """
    Modifica las fechas de un evento existente en el calendario indicado.
    """
    body = {"start": {"dateTime": start_iso, "timeZone": tz}, "end": {"dateTime": end_iso, "timeZone": tz}}
    try:
        evt = svc.events().patch(calendarId=calendar_id, eventId=event_id, body=body).execute()
        print(json.dumps({"id": evt["id"], "updated": evt.get("updated")}, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"ERROR modificando evento: {e}", file=sys.stderr)

def delete_event(svc, calendar_id: str, event_id: str):
    """
    Elimina un evento del calendario indicado.
    """
    try:
        svc.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        print(json.dumps({"deleted": event_id}, ensure_ascii=False))
    except Exception as e:
        print(f"ERROR eliminando evento: {e}", file=sys.stderr)

def _iso(s: str) -> str:
    """
    Valida y normaliza la fecha/hora en formato ISO 8601.
    Si la fecha no incluye zona horaria, la añade usando la variable TZ.
    """
    try:
        # Si la fecha es tipo 'YYYY-MM-DDTHH:MM' o 'YYYY-MM-DDTHH:MM:SS'
        dt = None
        if len(s) == 16:
            dt = datetime.strptime(s, "%Y-%m-%dT%H:%M")
        elif len(s) == 19:
            dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
        else:
            # Si ya tiene zona, solo validamos
            datetime.fromisoformat(s.replace("Z", "+00:00"))
        # Si no tiene zona horaria, la añadimos
        if dt:
            tz = os.getenv("TZ", "Europe/Madrid")
            # Mapeo simple de TZ a offset, solo para los casos comunes
            tz_offsets = {
                "Europe/Madrid": "+02:00", # Verano, ajustar si es invierno
                "Europe/London": "+01:00",
                "UTC": "+00:00",
            }
            offset = tz_offsets.get(tz, "+02:00")
            s = s + offset
    except Exception as e:
        raise argparse.ArgumentTypeError(f"Fecha/hora inválida: {s}. Usa ISO 8601. Error: {e}")
    return s

def list_events(svc, calendar_id: str, time_min: str, time_max: str, tz: str) -> List[Dict]:
    """Lista eventos entre dos fechas ISO y devuelve una lista simplificada."""
    events: List[Dict] = []
    page_token = None
    while True:
        resp = svc.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            pageToken=page_token,
            timeZone=tz,
        ).execute()
        for it in resp.get("items", []):
            events.append({
                "id": it.get("id"),
                "summary": it.get("summary"),
                "start": it.get("start", {}).get("dateTime") or it.get("start", {}).get("date"),
                "end": it.get("end", {}).get("dateTime") or it.get("end", {}).get("date"),
                "private": it.get("extendedProperties", {}).get("private", {}),
            })
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    print(json.dumps(events, indent=2, ensure_ascii=False))
    return events

def purge_day_events(svc, calendar_id: str, day_iso: str, tz: str, summary_prefix: str = "Reserva:") -> None:
    """Borra eventos de un día cuyo summary empiece por prefix o tengan private.reservation_id."""
    start_iso = _iso(f"{day_iso}T00:00:00")
    end_iso = _iso(f"{day_iso}T23:59:59")
    evs = list_events(svc, calendar_id, start_iso, end_iso, tz)
    to_delete = [e for e in evs if (str(e.get("summary") or "").startswith(summary_prefix) or e.get("private", {}).get("reservation_id"))]
    deleted = 0
    for e in to_delete:
        try:
            svc.events().delete(calendarId=calendar_id, eventId=e["id"]).execute()
            deleted += 1
        except Exception as ex:
            print(f"ERROR borrando {e['id']}: {ex}", file=sys.stderr)
    print(json.dumps({"deleted": deleted}, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description="Google Calendar smoke test")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_common(p):
        p.add_argument("--calendar", default=os.getenv("GCAL_TEST_CALENDAR_ID", ""), help="Calendar ID destino")
        p.add_argument("--tz", default=os.getenv("TZ", "Europe/Madrid"), help="Zona horaria")

    p_list = sub.add_parser("list-calendars", help="Listar calendarios")
    p_fb = sub.add_parser("freebusy", help="Consultar ocupado/libre")
    add_common(p_fb)
    p_fb.add_argument("--start", required=True, type=_iso)
    p_fb.add_argument("--end", required=True, type=_iso)

    p_create = sub.add_parser("create", help="Crear evento")
    add_common(p_create)
    p_create.add_argument("--start", required=True, type=_iso)
    p_create.add_argument("--end", required=True, type=_iso)
    p_create.add_argument("--summary", required=True)
    p_create.add_argument("--meta", default="", help='JSON para extendedProperties.private')

    p_patch = sub.add_parser("patch", help="Reprogramar evento")
    add_common(p_patch)
    p_patch.add_argument("--event-id", required=True)
    p_patch.add_argument("--start", required=True, type=_iso)
    p_patch.add_argument("--end", required=True, type=_iso)

    p_del = sub.add_parser("delete", help="Borrar evento")
    add_common(p_del)
    p_del.add_argument("--event-id", required=True)

    # Utilidades de consulta y mantenimiento
    p_list_ev = sub.add_parser("list-events", help="Listar eventos por rango de fechas")
    add_common(p_list_ev)
    p_list_ev.add_argument("--start", required=True, type=_iso)
    p_list_ev.add_argument("--end", required=True, type=_iso)

    p_purge_day = sub.add_parser("purge-day", help="Borrar eventos de un día (summary 'Reserva:' o con reservation_id)")
    add_common(p_purge_day)
    p_purge_day.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_purge_day.add_argument("--summary-prefix", default="Reserva:")

    p_purge_db = sub.add_parser("purge-db", help="Borrar todas las reservas locales (SQLite)")
    default_db_url = f"sqlite:///{(_here / 'pelubot.db').as_posix()}"
    p_purge_db.add_argument("--database-url", default=os.getenv("DATABASE_URL", default_db_url))

    # Sync de eventos -> DB
    p_sync = sub.add_parser("sync-from-gcal", help="Importar eventos de Google Calendar a la base de datos (upsert)")
    p_sync.add_argument("--by-professional", action="store_true", help="Usar mapeo PRO_CALENDAR por profesional")
    add_common(p_sync)
    p_sync.add_argument("--professional", default="", help="ID del profesional si no se usa --by-professional")
    p_sync.add_argument("--day", help="YYYY-MM-DD (alternativa a rango)")
    p_sync.add_argument("--start-date", help="YYYY-MM-DD")
    p_sync.add_argument("--end-date", help="YYYY-MM-DD")
    p_sync.add_argument("--default-service", default="corte", help="Servicio por defecto si no se detecta del summary/meta")
    p_sync.add_argument("--database-url", default=os.getenv("DATABASE_URL", default_db_url))

    args = parser.parse_args()
    # Comandos DB no necesitan cliente Google
    if args.cmd == "purge-db":
        # Purga tabla ReservationDB
        try:
            # Asegura que importamos los módulos del directorio 'Pelubot'
            if str(_here) not in sys.path:
                sys.path.insert(0, str(_here))
            from sqlmodel import create_engine, Session, SQLModel
            from sqlalchemy import delete as sa_delete
            import models  # asegura metadata
            from models import ReservationDB
            engine = create_engine(
                args.database_url,
                connect_args={"check_same_thread": False} if args.database_url.startswith("sqlite") else {},
            )
            # Crea tablas si no existen
            SQLModel.metadata.create_all(engine)
            with Session(engine) as s:
                s.exec(sa_delete(ReservationDB))
                s.commit()
            print(json.dumps({"ok": True, "message": "Reservas borradas"}))
        except Exception as e:
            print(json.dumps({"ok": False, "error": str(e)}))
        return

    # --- helper interno para sync-from-gcal ---
    def _parse_iso_to_dt(s: str) -> datetime:
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            # Si viene solo fecha, la tratamos como inicio del día en local
            return datetime.fromisoformat(s + "T00:00:00+00:00")

    def _detect_service(summary: str, default_sid: str) -> str:
        if not summary:
            return default_sid
        s = summary.lower()
        if "tinte" in s:
            return "tinte"
        if "barba" in s:
            return "barba"
        if "corte" in s:
            return "corte"
        return default_sid

    if args.cmd == "sync-from-gcal":
        # Carga dependencias de la app
        if str(_here) not in sys.path:
            sys.path.insert(0, str(_here))
        try:
            from sqlmodel import create_engine, Session
            from models import ReservationDB
            from data import PRO_CALENDAR
        except Exception as e:
            print(json.dumps({"ok": False, "error": f"Imports app fallidos: {e}"}))
            return

        # Rango de fechas
        tz = args.tz
        if args.day:
            try:
                day = date.fromisoformat(args.day)
            except Exception:
                print(json.dumps({"ok": False, "error": "--day inválido (YYYY-MM-DD)"}))
                return
            start_iso = _iso(f"{args.day}T00:00:00")
            end_iso = _iso(f"{args.day}T23:59:59")
            days: List[Tuple[str, str, date]] = [(start_iso, end_iso, day)]
        else:
            if not args.start_date or not args.end_date:
                print(json.dumps({"ok": False, "error": "Indica --day o --start-date y --end-date"}))
                return
            try:
                start_d = date.fromisoformat(args.start_date)
                end_d = date.fromisoformat(args.end_date)
            except Exception:
                print(json.dumps({"ok": False, "error": "Fechas inválidas (YYYY-MM-DD)"}))
                return
            if end_d < start_d:
                print(json.dumps({"ok": False, "error": "end-date < start-date"}))
                return
            days = []
            cur = start_d
            while cur <= end_d:
                days.append((_iso(f"{cur.isoformat()}T00:00:00"), _iso(f"{cur.isoformat()}T23:59:59"), cur))
                cur += timedelta(days=1)

        svc = build_calendar()
        # Preparar destino DB
        database_url = args.database_url
        from sqlmodel import create_engine
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
        )

        def _upsert_events(calendar_id: str, pro_id: str) -> Tuple[int, int]:
            inserted = 0
            updated = 0
            with Session(engine) as sess:
                for start_iso, end_iso, on_day in days:
                    evs = list_events(svc, calendar_id, start_iso, end_iso, tz)
                    for e in evs:
                        start_dt = _parse_iso_to_dt(e["start"])
                        end_dt = _parse_iso_to_dt(e["end"])
                        meta = e.get("private") or {}
                        rid = meta.get("reservation_id") or f"gcal:{e['id']}"
                        service_id = meta.get("service_id") or _detect_service(e.get("summary") or "", args.default_service)
                        pro = meta.get("professional_id") or pro_id or args.professional or ""
                        if not pro:
                            # sin profesional no podemos sincronizar
                            continue
                        r = sess.get(ReservationDB, rid)
                        if r is None:
                            r = ReservationDB(
                                id=rid,
                                service_id=service_id,
                                professional_id=pro,
                                start=start_dt,
                                end=end_dt,
                                google_event_id=e["id"],
                                google_calendar_id=calendar_id,
                            )
                            sess.add(r)
                            inserted += 1
                        else:
                            # actualizar mínimos si cambiaron
                            changed = False
                            if r.start != start_dt:
                                r.start = start_dt
                                changed = True
                            if r.end != end_dt:
                                r.end = end_dt
                                changed = True
                            if r.professional_id != pro:
                                r.professional_id = pro
                                changed = True
                            if r.service_id != service_id:
                                r.service_id = service_id
                                changed = True
                            if r.google_event_id != e["id"]:
                                r.google_event_id = e["id"]
                                changed = True
                            if r.google_calendar_id != calendar_id:
                                r.google_calendar_id = calendar_id
                                changed = True
                            if changed:
                                sess.add(r)
                                updated += 1
                    sess.commit()
            return inserted, updated

        total_ins = 0
        total_upd = 0
        if args.by_professional:
            for pro_id, cal_id in PRO_CALENDAR.items():
                ins, upd = _upsert_events(cal_id, pro_id)
                total_ins += ins
                total_upd += upd
        else:
            cal_id = args.calendar
            if not cal_id:
                print("ERROR: Debes indicar --calendar o usar --by-professional", file=sys.stderr)
                sys.exit(2)
            ins, upd = _upsert_events(cal_id, args.professional or "")
            total_ins += ins
            total_upd += upd
        print(json.dumps({"ok": True, "inserted": total_ins, "updated": total_upd}))
        return

    svc = build_calendar()

    if args.cmd == "list-calendars":
        list_calendars(svc)
        return
    if args.cmd in ("freebusy", "create", "patch", "delete", "list-events", "purge-day") and not args.calendar:
        print("ERROR: Debes indicar --calendar o exportar GCAL_TEST_CALENDAR_ID", file=sys.stderr)
        sys.exit(2)

    if args.cmd == "freebusy":
        freebusy(svc, args.calendar, args.start, args.end, args.tz)
    elif args.cmd == "create":
        private = {}
        if args.meta:
            try:
                private = json.loads(args.meta)
            except Exception as e:
                print(f"WARNING: meta inválido, ignorando. {e}", file=sys.stderr)
        create_event(svc, args.calendar, args.start, args.end, args.summary, args.tz, private)
    elif args.cmd == "patch":
        patch_event(svc, args.calendar, args.event_id, args.start, args.end, args.tz)
    elif args.cmd == "delete":
        delete_event(svc, args.calendar, args.event_id)
    elif args.cmd == "list-events":
        list_events(svc, args.calendar, args.start, args.end, args.tz)
    elif args.cmd == "purge-day":
        purge_day_events(svc, args.calendar, args.date, args.tz, args.summary_prefix)

if __name__ == "__main__":
    main()
