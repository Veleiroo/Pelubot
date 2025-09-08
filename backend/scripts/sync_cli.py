"""
One-off CLI to sync Google Calendar events into the local DB over a date range.

Usage examples:
  # default: today..today+6 (7 days)
  python -m backend.scripts.sync_cli

  # custom range
  START=2025-09-06 END=2025-09-13 python -m backend.scripts.sync_cli

  # days ahead (overrides END)
  DAYS=14 python -m backend.scripts.sync_cli

Environment:
  - USE_GCAL_BUSY, GCAL_CALENDAR_ID, GOOGLE_OAUTH_JSON, GOOGLE_SERVICE_ACCOUNT_JSON
  - TZ (default Europe/Madrid)
"""
from __future__ import annotations
import os
from datetime import date, timedelta

from dotenv import load_dotenv
load_dotenv()

from sqlmodel import Session, select

from app.db import engine, create_db_and_tables
from app.services.logic import sync_from_gcal_range, reconcile_db_to_gcal_range
from app.models import ReservationDB


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    return date.fromisoformat(s)


def main() -> None:
    create_db_and_tables()

    start_env = os.getenv("START")
    end_env = os.getenv("END")
    days_env = os.getenv("DAYS")

    if start_env:
        start = _parse_date(start_env)
    else:
        start = date.today()

    if end_env:
        end = _parse_date(end_env)
    else:
        days = int(days_env) if (days_env and days_env.isdigit()) else 7
        end = start + timedelta(days=max(0, days - 1))

    by_professional = (os.getenv("BY_PROFESSIONAL", "true").lower() in ("1","true","yes","y","si","sí"))
    calendar_id = os.getenv("CALENDAR_ID")
    professional_id = os.getenv("PROFESSIONAL_ID")
    default_service = os.getenv("DEFAULT_SERVICE_FOR_SYNC", "corte")

    mode = (os.getenv("MODE") or "import").lower()  # import | push | both
    with Session(engine) as s:
        before = s.exec(select(ReservationDB)).all()
        print(f"Reservations before: {len(before)}")

        results: dict[str, dict] = {}
        if mode in ("import", "both"):
            results["import"] = sync_from_gcal_range(
                s,
                start,
                end,
                default_service=default_service,
                by_professional=by_professional,
                calendar_id=calendar_id,
                professional_id=professional_id,
            )
        if mode in ("push", "both"):
            results["push"] = reconcile_db_to_gcal_range(
                s,
                start,
                end,
                by_professional=by_professional,
                calendar_id=calendar_id,
                professional_id=professional_id,
            )

        after = s.exec(select(ReservationDB)).all()

    print({
        "range": (start.isoformat(), end.isoformat()),
        "by_professional": by_professional,
        "mode": mode,
        "results": results,
        "reservations_after": len(after),
    })


if __name__ == "__main__":
    main()
