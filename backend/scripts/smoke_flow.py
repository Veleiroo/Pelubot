#!/usr/bin/env python3
"""
Smoke flow end-to-end:
1) Get slots (SERVICE_ID, PROFESSIONAL_ID, DAYS_AHEAD)
2) Create reservation
3) Reschedule to next slot
4) Cancel reservation
5) Run sync (both) for that day
6) Show conflicts for that day

Env vars:
  BASE=http://127.0.0.1:8776
  API_KEY=dev-key
  SERVICE_ID=corte
  PROFESSIONAL_ID=ana
  DAYS_AHEAD=10
"""
from __future__ import annotations
import json
import os
from urllib import request
from datetime import date, timedelta

BASE = os.getenv("BASE", "http://127.0.0.1:8776")
API_KEY = os.getenv("API_KEY", "dev-key")
SERVICE_ID = os.getenv("SERVICE_ID", "corte")
PROFESSIONAL_ID = os.getenv("PROFESSIONAL_ID", "ana")
DAYS_AHEAD = int(os.getenv("DAYS_AHEAD", "10"))


def _get(path: str):
    with request.urlopen(BASE + path) as r:
        return json.loads(r.read().decode())


def _post(path: str, payload: dict | None = None, headers: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode()
    req = request.Request(BASE + path, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    with request.urlopen(req) as r:
        return json.loads(r.read().decode())


def next_workday(days: int) -> date:
    d = date.today() + timedelta(days=days)
    while d.weekday() == 6:
        d += timedelta(days=1)
    return d


def main() -> None:
    out = {"health": _get("/health"), "ready": _get("/ready")}
    d = next_workday(DAYS_AHEAD)
    slots = _post(
        "/slots",
        {"service_id": SERVICE_ID, "date_str": d.isoformat(), "professional_id": PROFESSIONAL_ID},
    )
    arr = slots.get("slots") or []
    out["slots"] = len(arr)
    if len(arr) < 2:
        print(json.dumps({"ok": False, "error": "need at least 2 slots", **out}))
        return
    first, second = arr[0], arr[1]
    created = _post(
        "/reservations",
        {"service_id": SERVICE_ID, "professional_id": PROFESSIONAL_ID, "start": first},
        headers={"X-API-Key": API_KEY},
    )
    out["created"] = created
    res_id = created["message"].split("ID: ")[1].split(",")[0]
    rescheduled = _post(
        "/reservations/reschedule",
        {"reservation_id": res_id, "new_start": second},
        headers={"X-API-Key": API_KEY},
    )
    out["rescheduled"] = rescheduled
    cancelled = _post(
        "/reservations/" + res_id,
        None,
        headers={"X-API-Key": API_KEY, "X-HTTP-Method-Override": "DELETE"},
    )
    # If method override not supported, call cancel endpoint
    if not cancelled.get("ok"):
        cancelled = _post(
            "/cancel_reservation",
            {"reservation_id": res_id},
            headers={"X-API-Key": API_KEY},
        )
    out["cancelled"] = cancelled
    # Sync and conflicts
    day = first.split("T")[0]
    out["sync"] = _post(
        "/admin/sync",
        {"mode": "both", "start": day, "end": day},
        headers={"X-API-Key": API_KEY},
    )
    out["conflicts"] = _post(
        "/admin/conflicts",
        {"start": day, "end": day},
        headers={"X-API-Key": API_KEY},
    )
    print(json.dumps(out))


if __name__ == "__main__":
    main()

