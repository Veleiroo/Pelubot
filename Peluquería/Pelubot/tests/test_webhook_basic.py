def test_whatsapp_webhook_prices(app_client, monkeypatch):
    sent = []
    # stub de envío
    def fake_send(to, body):
        sent.append((to, body))
    # parchear función de envío en routes
    import routes
    monkeypatch.setattr(routes, "send_whatsapp_message", fake_send, raising=True)

    # enviar "precios"
    form = {"From": "whatsapp:+34123456789", "Body": "Precios"}
    r = app_client.post("/whatsapp/webhook", data=form)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert sent and "Precios:" in sent[-1][1]
