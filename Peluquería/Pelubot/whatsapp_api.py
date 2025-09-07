# whatsapp_api.py
"""
Módulo para enviar mensajes de WhatsApp usando Twilio API.
Incluye función para enviar mensajes desde la aplicación.
"""
from twilio.rest import Client
import os

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_whatsapp_message(to: str, body: str) -> None:
    """
    Envía un mensaje de WhatsApp usando Twilio.
    Args:
        to: Número destino en formato 'whatsapp:+34XXXXXXXXX'
        body: Texto del mensaje
    """
    client.messages.create(
        body=body,
        from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
        to=f"whatsapp:{to}"
    )

