# google_calendar.py
from __future__ import annotations
from typing import Dict, Any, Optional, List

# --- Carga .env para disponer de las credenciales en FastAPI/CLI ---
from dotenv import load_dotenv  # pip install python-dotenv
load_dotenv()

from google.oauth2.service_account import Credentials as SA
from google.oauth2.credentials import Credentials as UserCreds
from google.auth.transport.requests import Request  # para refrescar tokens OAuth
from googleapiclient.discovery import build

import json
import os

# --- Utilidad para normalizar fechas ISO con zona horaria ---
from datetime import datetime
try:
    from zoneinfo import ZoneInfo  # Py>=3.9
except Exception:
    ZoneInfo = None

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def iso_datetime(dt_or_str, tz: str = "Europe/Madrid") -> str:
    """
    Devuelve ISO 8601 con zona horaria real (RFC3339).
    - Acepta datetime o string.
    - Si el string ya trae offset/Z, lo deja tal cual.
    - Si no trae TZ, aplica el offset correcto del día usando zoneinfo.
    """
    if isinstance(dt_or_str, datetime):
        dt = dt_or_str
        if dt.tzinfo is None and ZoneInfo:
            dt = dt.replace(tzinfo=ZoneInfo(tz))
        return dt.isoformat()

    s = str(dt_or_str).strip()
    # si ya tiene Z u offset, lo dejamos
    if s.endswith("Z") or ("+" in s[10:] or "-" in s[10:]):
        return s

    # intentar parsear string "YYYY-MM-DDTHH:MM" o "...:SS"
    fmt = "%Y-%m-%dT%H:%M:%S" if len(s) == 19 else "%Y-%m-%dT%H:%M"
    dt = datetime.strptime(s, fmt)
    if ZoneInfo:
        dt = dt.replace(tzinfo=ZoneInfo(tz))
        return dt.isoformat()
    # fallback si no hay zoneinfo (no ideal): añade +02:00
    return s + "+02:00"

def _load_sa_creds() -> Optional[SA]:
    """
    Carga Service Account desde GOOGLE_SERVICE_ACCOUNT_JSON (ruta o JSON inline).
    Si se indica GOOGLE_IMPERSONATE_EMAIL, usa impersonación.
    """
    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        return None
    info = json.loads(sa_json) if sa_json.strip().startswith("{") else json.load(open(sa_json, "r", encoding="utf-8"))
    creds = SA.from_service_account_info(info, scopes=SCOPES)
    subject = os.getenv("GOOGLE_IMPERSONATE_EMAIL")
    if subject:
        creds = creds.with_subject(subject)
    return creds

def _load_user_creds() -> Optional[UserCreds]:
    """
    Carga OAuth de usuario desde GOOGLE_OAUTH_JSON (ruta o JSON inline).
    Si no está definida, intenta 'oauth_tokens.json' en el directorio del proyecto (fallback).
    Refresca el token si está caducado y hay refresh_token.
    """
    oa_json = os.getenv("GOOGLE_OAUTH_JSON")
    if not oa_json:
        # Fallback: archivo local 'oauth_tokens.json'
        here = os.path.dirname(__file__)
        candidate = os.path.join(here, "oauth_tokens.json")
        if os.path.exists(candidate):
            oa_json = candidate
        else:
            return None

    # Si es JSON inline, úsalo directamente
    if oa_json.strip().startswith("{"):
        info = json.loads(oa_json)
    else:
        # Resolver ruta de forma robusta evitando duplicar 'Pelubot/'
        from pathlib import Path
        p = Path(oa_json)
        here = Path(__file__).resolve().parent
        candidates = []
        if p.is_absolute():
            candidates.append(p)
        else:
            # 1) relativa al CWD
            candidates.append(Path(os.getcwd()) / p)
            # 2) relativa a la raíz del proyecto (padre del módulo)
            candidates.append(here.parent / p)
            # 3) relativa al propio directorio del módulo
            candidates.append(here / p)
            # 4) solo el nombre en el directorio del módulo
            candidates.append(here / p.name)
        path = None
        for cand in candidates:
            try:
                if cand.exists():
                    path = cand
                    break
            except Exception:
                continue
        if path is None:
            # último intento: usar la ruta tal cual
            path = p if p.is_absolute() else (Path(os.getcwd()) / p)
        info = json.load(open(path, "r", encoding="utf-8"))

    creds = UserCreds.from_authorized_user_info(info, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        # refrescamos para evitar 401 por expiración
        creds.refresh(Request())
    return creds

# --- Clientes falsos para tests ---
class _FakeFreebusy:
    def __init__(self):
        self._body = None
    def query(self, body):
        self._body = body
        return self
    def execute(self):
        # Devuelve siempre sin ocupados
        cal_id = None
        try:
            items = (self._body or {}).get("items", [])
            if items:
                cal_id = items[0].get("id")
        except Exception:
            pass
        return {"calendars": {cal_id or "primary": {"busy": []}}}

class _FakeEventsOp:
    def __init__(self, result):
        self._result = result
    def execute(self):
        return self._result

class _FakeEvents:
    def __init__(self, store: dict):
        self._store = store
    def insert(self, calendarId: str, body: dict):
        event_id = f"fake-{len(self._store) + 1}"
        self._store[event_id] = {**body, "id": event_id, "calendarId": calendarId}
        return _FakeEventsOp({"id": event_id})
    def patch(self, calendarId: str, eventId: str, body: dict):
        ev = self._store.get(eventId, {"id": eventId, "calendarId": calendarId})
        ev.update(body)
        self._store[eventId] = ev
        return _FakeEventsOp({"id": eventId})
    def delete(self, calendarId: str, eventId: str):
        self._store.pop(eventId, None)
        return _FakeEventsOp({})
    def list(self, calendarId: str, timeMin: str, timeMax: str, singleEvents: bool = True, orderBy: str = "startTime", pageToken: Optional[str] = None, timeZone: Optional[str] = None):
        # Devuelve vacío por defecto en tests
        return _FakeEventsOp({"items": []})

class FakeCalendarService:
    def __init__(self):
        self._events_store: dict[str, dict] = {}
    def freebusy(self):
        return _FakeFreebusy()
    def events(self):
        return _FakeEvents(self._events_store)
    def calendarList(self):
        class _CL:
            def list(self_inner):
                return _FakeEventsOp({"items": []})
        return _CL()

# --- Autenticación y cliente ---
def build_calendar() -> Any:
    """
    Crea el cliente de Calendar.
    Prioriza SERVICE ACCOUNT y, si no, OAuth de usuario (con fallback a oauth_tokens.json local).
    En entorno de test (pytest) o si PELUBOT_FAKE_GCAL=1, devuelve un cliente falso.
    """
    # En tests, siempre cliente falso para evitar dependencias externas
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("PELUBOT_FAKE_GCAL") == "1":
        return FakeCalendarService()

    try:
        sa = _load_sa_creds()
        if sa:
            return build("calendar", "v3", credentials=sa)

        oa = _load_user_creds()
        if oa:
            return build("calendar", "v3", credentials=oa)
    except Exception as e:
        # Si estamos en tests, usa fake
        if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("PELUBOT_FAKE_GCAL") == "1":
            return FakeCalendarService()
        raise RuntimeError(f"Error al crear cliente de Google Calendar: {e}")

    # Sin credenciales: en tests, usa fake; en prod, error
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("PELUBOT_FAKE_GCAL") == "1":
        return FakeCalendarService()
    raise RuntimeError("No hay credenciales. Exporta GOOGLE_SERVICE_ACCOUNT_JSON o GOOGLE_OAUTH_JSON")

# --- Operaciones principales ---
def freebusy(service: Any, calendar_id: str, time_min_iso: str, time_max_iso: str, tz: str = "Europe/Madrid") -> List[Dict[str, str]]:
    """
    Consulta los intervalos ocupados (busy) en el calendario indicado entre dos fechas ISO.
    Devuelve lista de rangos {"start": ..., "end": ...}
    """
    body = {
        "timeMin": iso_datetime(time_min_iso, tz),
        "timeMax": iso_datetime(time_max_iso, tz),
        "timeZone": tz,
        "items": [{"id": calendar_id}],
    }
    try:
        fb = service.freebusy().query(body=body).execute()
        cals = fb.get("calendars", {})
        busy = cals.get(calendar_id, {}).get("busy", [])
        return busy
    except Exception as e:
        raise RuntimeError(f"Error consultando freebusy: {e}")

# --- Listar calendarios ---
def list_calendars(service: Any) -> List[Dict[str, Any]]:
    """
    Lista todos los calendarios accesibles por el usuario o service account.
    Devuelve lista de calendarios.
    """
    try:
        items = service.calendarList().list().execute().get("items", [])
        return items
    except Exception as e:
        raise RuntimeError(f"Error listando calendarios: {e}")

def create_event(service: Any, calendar_id: str, start_dt, end_dt, summary: str, private_props: Dict[str, str] = None, color_id: Optional[str] = None, tz: str = "Europe/Madrid") -> Dict[str, Any]:
    """
    Crea un evento en el calendario indicado.
    Permite añadir propiedades privadas y color.
    Devuelve el evento creado.
    """
    if private_props is None:
        private_props = {}
    body = {
        "summary": summary,
        "start": {"dateTime": iso_datetime(start_dt, tz), "timeZone": tz},
        "end": {"dateTime": iso_datetime(end_dt, tz), "timeZone": tz},
        "extendedProperties": {"private": private_props},
    }
    if color_id:
        body["colorId"] = color_id
    try:
        return service.events().insert(calendarId=calendar_id, body=body).execute()
    except Exception as e:
        raise RuntimeError(f"Error creando evento: {e}")

def patch_event(service: Any, calendar_id: str, event_id: str, start_dt, end_dt, tz: str = "Europe/Madrid") -> Dict[str, Any]:
    """
    Modifica las fechas de un evento existente en el calendario indicado.
    Devuelve el evento actualizado.
    """
    body = {
        "start": {"dateTime": iso_datetime(start_dt, tz), "timeZone": tz},
        "end": {"dateTime": iso_datetime(end_dt, tz), "timeZone": tz},
    }
    try:
        return service.events().patch(calendarId=calendar_id, eventId=event_id, body=body).execute()
    except Exception as e:
        raise RuntimeError(f"Error modificando evento: {e}")

def delete_event(service: Any, calendar_id: str, event_id: str) -> None:
    """
    Elimina un evento del calendario indicado.
    """
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    except Exception as e:
        raise RuntimeError(f"Error eliminando evento: {e}")

def list_events_range(service: Any, calendar_id: str, time_min_iso: str, time_max_iso: str, tz: str = "Europe/Madrid") -> List[Dict[str, Any]]:
    """
    Lista eventos de un calendario en un rango [time_min, time_max].
    Devuelve items con id, summary, start, end y extendedProperties.private si existe.
    """
    try:
        resp = service.events().list(
            calendarId=calendar_id,
            timeMin=iso_datetime(time_min_iso, tz),
            timeMax=iso_datetime(time_max_iso, tz),
            singleEvents=True,
            orderBy="startTime",
            timeZone=tz,
        ).execute()
        items = resp.get("items", [])
        return items
    except Exception as e:
        raise RuntimeError(f"Error listando eventos: {e}")
