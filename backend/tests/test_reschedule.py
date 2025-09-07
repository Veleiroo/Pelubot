from datetime import date, timedelta

API_KEY = "test-api-key"

def test_reschedule_flow(app_client, monkeypatch):
    # buscar un día laborable
    target = date.today() + timedelta(days=32)
    while target.weekday() == 6:
        target += timedelta(days=1)

    # slots
    r = app_client.post("/slots", json={"service_id": "corte", "date_str": target.isoformat(), "professional_id": "luis"})
    assert r.status_code == 200
    slots = r.json()["slots"]
    assert len(slots) >= 2
    start, new_start = slots[0], slots[1]

    # crear
    create_payload = {"service_id": "corte", "professional_id": "luis", "start": start}
    r = app_client.post("/reservations", headers={"X-API-Key": API_KEY}, json=create_payload)
    assert r.status_code == 200
    msg = r.json()["message"]
    res_id = msg.split("ID: ")[1].split(",")[0]

    # reprogramar
    resched_payload = {"reservation_id": res_id, "new_start": new_start}
    r2 = app_client.post("/reservations/reschedule", headers={"X-API-Key": API_KEY}, json=resched_payload)
    assert r2.status_code == 200
    assert r2.json()["ok"] is True
    assert "Reprogramada" in r2.json()["message"]
