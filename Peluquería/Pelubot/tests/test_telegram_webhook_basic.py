from fastapi.testclient import TestClient

API_KEY = "test-api-key"


def _tg_update(text: str, chat_id: int = 12345):
    return {"message": {"chat": {"id": chat_id}, "text": text}}


def test_telegram_webhook_horario(app_client, monkeypatch):
    import telegram_api
    sent = {}

    async def fake_send(chat_id, text):
        sent["last"] = (chat_id, text)

    monkeypatch.setattr(telegram_api, "send_telegram_message", fake_send)

    r = app_client.post("/telegram/webhook", json=_tg_update("horario"))
    assert r.status_code == 200
    assert sent and "Abrimos" in sent["last"][1]


def test_telegram_webhook_precios(app_client, monkeypatch):
    import telegram_api
    sent = {}

    async def fake_send(chat_id, text):
        sent["last"] = (chat_id, text)

    monkeypatch.setattr(telegram_api, "send_telegram_message", fake_send)

    r = app_client.post("/telegram/webhook", json=_tg_update("precios"))
    assert r.status_code == 200
    assert sent and "Precios" in sent["last"][1]

