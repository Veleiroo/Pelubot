# telegram_api.py
import os
import httpx

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

class TelegramConfigError(RuntimeError):
    pass

def _base_url() -> str:
    if not TELEGRAM_BOT_TOKEN:
        raise TelegramConfigError("Falta TELEGRAM_BOT_TOKEN en entorno")
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

async def send_telegram_message(chat_id: str | int, text: str) -> None:
    url = _base_url() + "/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(url, json=data)
            r.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Error enviando mensaje a Telegram: {e}")
