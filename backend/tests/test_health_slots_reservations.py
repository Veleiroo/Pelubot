from datetime import date, timedelta
import os

API_KEY = "test-api-key"
os.environ["API_KEY"] = API_KEY

def test_health(app_client):
    r = app_client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}

def test_slots_validation_errors(app_client):
    # formato de fecha incorrecto
    r = app_client.post("/slots", json={"service_id": "corte", "date_str": "06-09-2025"})
    assert r.status_code == 400
    assert "YYYY-MM-DD" in r.json()["detail"]
    # pasado
    r = app_client.post("/slots", json={"service_id": "corte", "date_str": "2024-01-01"})
    assert r.status_code == 400
    assert "pasado" in r.json()["detail"].lower()

def test_create_list_cancel_reservation_flow(app_client):
    # Fecha futura cercana (evitar domingo)
    target = date.today() + timedelta(days=30)
    while target.weekday() == 6:
        target += timedelta(days=1)

    # 1) obtener slots
    r = app_client.post("/slots", json={"service_id": "corte", "date_str": target.isoformat(), "professional_id": "ana"})
    assert r.status_code == 200
    slots = r.json()["slots"]
    assert isinstance(slots, list) and len(slots) > 0
    start = slots[0]

    # 2) crear reserva (requiere API Key)
    payload = {
        "service_id": "corte",
        "professional_id": "ana",
        "start": start
    }
    r = app_client.post("/reservations", headers={"X-API-Key": API_KEY}, json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ok"] is True
    # Extrae ID del mensaje "Reserva creada y sincronizada. ID: <id>, Evento: ..."
    res_id = data["message"].split("ID: ")[1].split(",")[0]

    # 3) conflictiva: volver a reservar el mismo slot debe fallar
    r2 = app_client.post("/reservations", headers={"X-API-Key": API_KEY}, json=payload)
    assert r2.status_code == 400
    assert "no está disponible" in r2.json()["detail"].lower()

    # 4) cancelar (DELETE)
    r3 = app_client.delete(f"/reservations/{res_id}", headers={"X-API-Key": API_KEY})
    assert r3.status_code == 200
    assert r3.json()["ok"] is True
