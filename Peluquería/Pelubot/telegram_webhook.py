import os
import hmac
import hashlib
import json
import httpx
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi import status
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel
from dotenv import load_dotenv
from data import PROS, SERVICES
import telegram_api  # para que el test pueda monkeypatchear el envío básico

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Falta TELEGRAM_BOT_TOKEN en .env")

TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip() or None

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

API_KEY = os.getenv("API_KEY", "").strip()

router = APIRouter(prefix="/telegram", tags=["telegram"])

# ──────────────────────────────────────────────────────────────────────────────
# Helpers Telegram
# ──────────────────────────────────────────────────────────────────────────────

async def tg_send(chat_id: int, text: str, reply_markup: Optional[dict] = None, parse_mode: Optional[str] = None):
    # Si no hay teclados ni formato especial, usa el cliente básico (facilita tests con monkeypatch)
    if reply_markup is None and parse_mode is None:
        try:
            await telegram_api.send_telegram_message(chat_id, text)
            return {"ok": True}
        except Exception:
            pass
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if parse_mode:
        payload["parse_mode"] = parse_mode

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{TELEGRAM_API}/sendMessage", json=payload)
        r.raise_for_status()
        return r.json()

async def tg_edit(chat_id: int, message_id: int, text: str, reply_markup: Optional[dict] = None):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{TELEGRAM_API}/editMessageText", json=payload)
        r.raise_for_status()
        return r.json()

def ik_row(*buttons: dict) -> List[List[dict]]:
    return [list(buttons)]

def ik_button(text: str, data: str) -> dict:
    # ojo: Telegram limita callback_data a 64 bytes
    return {"text": text, "callback_data": data[:64]}

def kb_menu() -> dict:
    return {"inline_keyboard": [
        [ik_button("💇 Reservar cita", "menu:reservar")],
        [ik_button("💸 Ver precios", "menu:precios")],
        [ik_button("🕒 Horario", "menu:horario")],
        [ik_button("📖 Mis reservas", "menu:misreservas")],
        [ik_button("❌ Cancelar reserva", "menu:cancelar")],
        [ik_button("👩‍💼 Hablar con humano", "menu:humano")],
    ]}

def kb_servicios() -> dict:
    # Genera botones desde SERVICES
    rows: List[List[dict]] = []
    row: List[dict] = []
    for s in SERVICES:
        row.append(ik_button(s.name, f"srv:{s.id}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([ik_button("⬅️ Volver", "back:menu")])
    return {"inline_keyboard": rows}

def kb_profesionales() -> dict:
    # Genera botones desde PROS
    rows: List[List[dict]] = []
    row: List[dict] = []
    for p in PROS:
        row.append(ik_button(p.name, f"pro:{p.id}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([ik_button("Cualquiera", "pro:any")])
    rows.append([ik_button("⬅️ Volver", "back:srv")])
    return {"inline_keyboard": rows}

def format_day(d: date) -> str:
    dias = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
    return f"{dias[d.weekday()]} {d.strftime('%d-%m')}"

def kb_fechas(base: Optional[date] = None) -> dict:
    base = base or date.today()
    opts = [base, base + timedelta(days=1), base + timedelta(days=2)]
    rows = []
    for d in opts:
        rows.append([ik_button(format_day(d), f"day:{d.isoformat()}")])
    rows.append([ik_button("⬅️ Volver", "back:pro")])
    return {"inline_keyboard": rows}

def kb_horas(slots: List[str]) -> dict:
    rows: List[List[dict]] = []
    # dos por fila
    row: List[dict] = []
    for s in slots:
        row.append(ik_button(s, f"time:{s}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([ik_button("⬅️ Volver", "back:day")])
    return {"inline_keyboard": rows}

# ──────────────────────────────────────────────────────────────────────────────
# Estado en memoria (simple) por chat
# ──────────────────────────────────────────────────────────────────────────────

class Session(BaseModel):
    step: str = "menu"
    service: Optional[str] = None
    professional: Optional[str] = None
    day: Optional[str] = None   # YYYY-MM-DD
    time: Optional[str] = None  # HH:MM
    welcomed: bool = False

SESSIONS: Dict[int, Session] = {}

def get_session(chat_id: int) -> Session:
    sess = SESSIONS.get(chat_id)
    if not sess:
        sess = Session()
        SESSIONS[chat_id] = sess
    return sess

def reset_session(chat_id: int):
    SESSIONS[chat_id] = Session()

# ──────────────────────────────────────────────────────────────────────────────
# Seguridad opcional: validar secret_token del webhook
# ──────────────────────────────────────────────────────────────────────────────

def _check_secret(req: Request):
    if TELEGRAM_WEBHOOK_SECRET:
        # header: X-Telegram-Bot-Api-Secret-Token
        token = req.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if token != TELEGRAM_WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="invalid secret")

# ──────────────────────────────────────────────────────────────────────────────
# Lógica de reservas: trae slots y crea reserva contra tu API
# (AJUSTA endpoints si ya tienes /slots y /reservations)
# ──────────────────────────────────────────────────────────────────────────────

async def fetch_slots(service_id: str, day_iso: str, pro: Optional[str]) -> List[str]:
    """
    Devuelve lista de horas 'HH:MM'. Ajustado al contrato real de /slots:
    POST /slots con {service_id, date_str, professional_id?} -> {"slots": ["ISO_DATETIME", ...]}
    """
    api = os.getenv("INTERNAL_API_BASE", "http://localhost:8000").rstrip("/")
    payload = {"service_id": service_id, "date_str": day_iso}
    if pro and pro != "any":
        payload["professional_id"] = pro
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{api}/slots", json=payload)
        if r.status_code != 200:
            # fallback: horas dummy si aún no está la API lista
            return ["10:00","10:30","11:00","12:00","16:00","16:30","17:00"]
        data = r.json()
        slots = data.get("slots") or []
        # normaliza a HH:MM a partir de ISO
        norm: List[str] = []
        for s in slots:
            if isinstance(s, str):
                if "T" in s:
                    tpart = s.split("T", 1)[1]
                else:
                    tpart = s
                norm.append(tpart[:5])
        return norm or ["10:00","10:30","11:00","12:00","16:00","16:30","17:00"]

async def _choose_pro_for_slot(service_id: str, day_iso: str, hhmm: str) -> Optional[str]:
    """Si el usuario eligió 'Cualquiera', elige un profesional que tenga ese hh:mm disponible."""
    for p in PROS:
        if service_id not in p.services:
            continue
        try:
            hours = await fetch_slots(service_id, day_iso, p.id)
            if hhmm in hours:
                return p.id
        except Exception:
            continue
    return None

async def create_reservation(service_id: str, pro: Optional[str], day_iso: str, hhmm: str, user_id: int) -> dict:
    """
    Crea la reserva en tu backend ajustando al contrato real: POST /reservations
    {service_id, professional_id, start}
    """
    api = os.getenv("INTERNAL_API_BASE", "http://localhost:8000").rstrip("/")
    # Resolver profesional si es "any" o None
    chosen_pro = None if (not pro or pro == "any") else pro
    if not chosen_pro:
        chosen_pro = await _choose_pro_for_slot(service_id, day_iso, hhmm)
    if not chosen_pro:
        return {"ok": False, "error": "No hay profesional disponible para esa hora."}

    # Construir inicio como ISO local (naive); el backend normaliza TZ
    start_dt = f"{day_iso}T{hhmm}"
    payload = {
        "service_id": service_id,
        "professional_id": chosen_pro,
        "start": start_dt,
    }
    headers = {"X-API-Key": API_KEY} if API_KEY else {}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{api}/reservations", json=payload, headers=headers)
        if r.status_code != 200:
            return {"ok": False, "error": r.text}
        return {"ok": True, "data": r.json()}

# ──────────────────────────────────────────────────────────────────────────────
# Webhook
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/webhook")
async def telegram_webhook(request: Request):
    _check_secret(request)
    update = await request.json()

    # Mensajes de texto
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = (msg.get("text") or "").strip()
        body = text.lower()
        sess = get_session(chat_id)

        # Primer contacto o saludo: enviar saludo bonito con menú
        greetings = ("hola", "buenas", "buenos dias", "buenos días", "buenas tardes", "buenas noches", "hello", "hi", "hey")
        if (not sess.welcomed and text and any(g in body for g in greetings)):
            # Marcar como saludado para no repetir cada mensaje
            sess.welcomed = True
            welcome = (
                "¡Bienvenido/a a PeluBot! 💇\n\n"
                "Estoy aquí para ayudarte a reservar tu cita, ver precios y horarios, o ponerte en contacto con alguien del equipo.\n\n"
                "Elige una opción del menú de abajo o escribe 'horario' o 'precios'."
            )
            await tg_send(chat_id, welcome, kb_menu())
            return {"ok": True}

        # flujo de cancelación por texto
        if sess.step == "cancel" and text and not text.startswith("/"):
            api = os.getenv("INTERNAL_API_BASE", "http://localhost:8000").rstrip("/")
            headers = {"X-API-Key": API_KEY} if API_KEY else {}
            rid = text
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    r = await client.delete(f"{api}/reservations/{rid}", headers=headers)
                if r.status_code == 200:
                    reset_session(chat_id)
                    await tg_send(chat_id, f"✅ Reserva {rid} cancelada.", kb_menu())
                elif r.status_code == 404:
                    await tg_send(chat_id, "No encontré esa reserva. Revisa el ID o prueba con 'Mis reservas'.", kb_menu())
                else:
                    await tg_send(chat_id, f"No se pudo cancelar: {r.text}", kb_menu())
            except Exception as e:
                await tg_send(chat_id, "Error de red cancelando la reserva. Inténtalo de nuevo.", kb_menu())
            return {"ok": True}

        # comandos básicos por texto
        if text == "/start":
            reset_session(chat_id)
            welcome = (
                "¡Bienvenido/a a PeluBot! 💇\n\n"
                "Te ayudo a: reservar cita, ver precios, consultar horario o hablar con alguien del equipo.\n\n"
                "Elige una opción o escribe 'horario' o 'precios'."
            )
            await tg_send(chat_id, welcome, kb_menu())
            return {"ok": True}

        if "horario" in body:
            await tg_send(chat_id, "Abrimos L–V 10:00–14:00 y 16:00–20:00; sábados 10:00–14:00. Domingos cerrado.")
            return {"ok": True}

        if "precio" in body:
            parts = [f"- {s.name}: {s.price_eur:.2f}€" for s in SERVICES]
            await tg_send(chat_id, "Precios:\n" + "\n".join(parts))
            return {"ok": True}

        # Si el usuario escribe libremente durante flujo de reserva, puedes interpretarlo aquí.
        await tg_send(chat_id, "Elige una opción del menú:", kb_menu())
        return {"ok": True}

    # Pulsación de botones (inline keyboard)
    if "callback_query" in update:
        cq = update["callback_query"]
        data = cq.get("data") or ""
        chat_id = cq["message"]["chat"]["id"]
        message_id = cq["message"]["message_id"]
        sess = get_session(chat_id)

        # Navegación principal
        if data == "menu:reservar":
            sess.step = "srv"
            await tg_edit(chat_id, message_id, "Elige el servicio:", kb_servicios())
            return {"ok": True}

        if data == "menu:precios":
            parts = [f"• {s.name}: {s.price_eur:.2f}€" for s in SERVICES]
            txt = "💸 Precios:\n\n" + "\n".join(parts)
            await tg_edit(chat_id, message_id, txt, kb_menu())
            return {"ok": True}

        if data == "menu:horario":
            await tg_edit(chat_id, message_id, "Abrimos L–V 10:00–14:00 y 16:00–20:00; sábados 10:00–14:00. Domingos cerrado.", kb_menu())
            return {"ok": True}

        if data == "menu:misreservas":
            # Lista simple (primeras 5) con fecha/hora e ID
            api = os.getenv("INTERNAL_API_BASE", "http://localhost:8000").rstrip("/")
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    r = await client.get(f"{api}/reservations")
                    rows = r.json() if r.status_code == 200 else []
            except Exception:
                rows = []
            if not rows:
                await tg_edit(chat_id, message_id, "No hay reservas registradas por ahora.", kb_menu())
                return {"ok": True}
            lines = []
            for it in rows[:5]:
                start = it.get("start", "?")
                rid = it.get("id", "?")
                lines.append(f"• {start} — {rid}")
            await tg_edit(chat_id, message_id, "Tus últimas reservas:\n\n" + "\n".join(lines), kb_menu())
            return {"ok": True}

        if data == "menu:cancelar":
            sess.step = "cancel"
            await tg_edit(chat_id, message_id, "Escribe el ID de tu reserva para cancelarla:", kb_menu())
            return {"ok": True}

        if data == "menu:humano":
            await tg_edit(chat_id, message_id, "Te paso con una persona enseguida 👩‍💼", kb_menu())
            return {"ok": True}

        # Volver
        if data == "back:menu":
            reset_session(chat_id)
            await tg_edit(chat_id, message_id, "Elige una opción:", kb_menu())
            return {"ok": True}
        if data == "back:srv":
            sess.step = "srv"
            await tg_edit(chat_id, message_id, "Elige el servicio:", kb_servicios())
            return {"ok": True}
        if data == "back:pro":
            sess.step = "pro"
            await tg_edit(chat_id, message_id, "Elige la persona que te atenderá:", kb_profesionales())
            return {"ok": True}
        if data == "back:day":
            sess.step = "day"
            base = date.fromisoformat(sess.day) if sess.day else None
            await tg_edit(chat_id, message_id, "Elige un día:", kb_fechas(base))
            return {"ok": True}

        # Servicio elegido
        if data.startswith("srv:"):
            sess.service = data.split(":",1)[1]
            sess.step = "pro"
            await tg_edit(chat_id, message_id, "Elige la persona que te atenderá:", kb_profesionales())
            return {"ok": True}

        # Profesional elegido
        if data.startswith("pro:"):
            sess.professional = data.split(":",1)[1]
            sess.step = "day"
            await tg_edit(chat_id, message_id, "Elige un día:", kb_fechas())
            return {"ok": True}

        # Día elegido
        if data.startswith("day:"):
            sess.day = data.split(":",1)[1]  # YYYY-MM-DD
            sess.step = "time"

            slots = await fetch_slots(sess.service or "corte", sess.day, sess.professional)
            if not slots:
                await tg_edit(chat_id, message_id, "No hay horas disponibles para ese día. Elige otra fecha:", kb_fechas())
                return {"ok": True}

            await tg_edit(chat_id, message_id, f"Disponibilidad para *{sess.day}*:", kb_horas(slots))
            return {"ok": True}

        # Hora elegida → creamos reserva
        if data.startswith("time:"):
            sess.time = data.split(":",1)[1]  # HH:MM
            svc = sess.service or "corte"
            pro = sess.professional
            dy  = sess.day or date.today().isoformat()
            hhmm = sess.time

            result = await create_reservation(svc, pro, dy, hhmm, chat_id)
            if result.get("ok"):
                # El backend devuelve {ok, message}; extraer ID del texto
                msg = result["data"].get("message", "")
                rid = "—"
                if "ID: " in msg:
                    rid = msg.split("ID: ",1)[1].split(",",1)[0].strip()
                txt = (
                    "✅ *Reserva confirmada*\n\n"
                    f"• Servicio: {svc}\n"
                    f"• Profesional: {('Cualquiera' if (not pro or pro=='any') else pro)}\n"
                    f"• Fecha: {dy} {hhmm}\n"
                    f"• Nº de reserva: {rid}\n\n"
                    "¿Necesitas algo más?"
                )
                reset_session(chat_id)
                await tg_edit(chat_id, message_id, txt, kb_menu())
            else:
                err = result.get("error","Error inesperado")
                await tg_edit(chat_id, message_id, f"❌ No se pudo crear la reserva.\n\n{err}", kb_menu())
            return {"ok": True}

        # Fallback
        await tg_edit(chat_id, message_id, "No he entendido esa opción. Elige del menú:", kb_menu())
        return {"ok": True}

    # Si no es message ni callback_query, responde ok para que Telegram no reintente
    return {"ok": True}
