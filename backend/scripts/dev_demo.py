#!/usr/bin/env python3
"""
Dev demo helper:
- Optionally clears Google Calendars via admin endpoint
- Creates a demo reservation and checks conflicts

Env vars:
  BASE        default http://127.0.0.1:8776
  API_KEY     default dev-key
  SERVICE_ID  default corte
  PROFESSIONAL_ID default ana
  DAYS_AHEAD  default 10
  CLEAR_ALL   default true (if true, clear all events; if false, only pelubot events)

Usage:
  python backend/scripts/dev_demo.py            # clear+demo
  python backend/scripts/dev_demo.py --no-clear # only demo
  python backend/scripts/dev_demo.py --clear-only # only clear
"""
from __future__ import annotations
import json
import os
from datetime import date, timedelta
from urllib import request

BASE = os.getenv("BASE", "http://127.0.0.1:8776")
API_KEY = os.getenv("API_KEY", "dev-key")
SERVICE_ID = os.getenv("SERVICE_ID", "corte")
PROFESSIONAL_ID = os.getenv("PROFESSIONAL_ID", "ana")
DAYS_AHEAD = int(os.getenv("DAYS_AHEAD", "10"))
CLEAR_ALL = (os.getenv("CLEAR_ALL", "true").lower() in ("1","true","yes","y","si","sí"))


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


def clear_calendars():
    body = {
        "dry_run": False,
        "confirm": "DELETE",
        "only_pelubot": (not CLEAR_ALL and True) or False,
    }
    out = _post("/admin/clear_calendars", body, headers={"X-API-Key": API_KEY})
    return out


def demo_flow():
    d = next_workday(DAYS_AHEAD)
    slots = _post("/slots", {"service_id": SERVICE_ID, "date_str": d.isoformat(), "professional_id": PROFESSIONAL_ID})
    arr = slots.get("slots") or []
    if not arr:
        return {"ok": False, "error": "No slots available"}
    first = arr[0]
    created = _post(
        "/reservations",
        {"service_id": SERVICE_ID, "professional_id": PROFESSIONAL_ID, "start": first},
        headers={"X-API-Key": API_KEY},
    )
    conf = _post(
        "/admin/conflicts",
        {"start": first.split("T")[0], "end": first.split("T")[0]},
        headers={"X-API-Key": API_KEY},
    )
    return {"slots": len(arr), "created": created, "conflicts": conf}


def main():
    import sys
    do_clear = True
    clear_only = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "--no-clear":
            do_clear = False
        elif sys.argv[1] == "--clear-only":
            clear_only = True

    health = _get("/health")
    ready = _get("/ready")
    print(json.dumps({"health": health, "ready": ready}))

    if do_clear or clear_only:
        cleared = clear_calendars()
        print(json.dumps({"cleared": cleared}))
        if clear_only:
            return

    result = demo_flow()
    print(json.dumps(result))


if __name__ == "__main__":
    main()
