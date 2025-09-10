#!/usr/bin/env python3
"""Simple environment validator for Pelubot.

Checks presence of required variables and reports missing ones.
It does not reveal secret values.
"""
import os
import sys
from pathlib import Path

REQUIRED = [
    "API_KEY",
    "TZ",
    "ORIGINS",
    "GCAL_CALENDAR_ID",
]

EITHER = (
    "GOOGLE_OAUTH_JSON",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
)

def main() -> int:
    missing = [var for var in REQUIRED if not os.getenv(var)]
    if not any(os.getenv(v) for v in EITHER):
        missing.append("GOOGLE_OAUTH_JSON or GOOGLE_SERVICE_ACCOUNT_JSON")

    if missing:
        print("Missing variables:")
        for name in missing:
            print(f"- {name}")
        return 1

    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        if not Path(db_path).exists():
            print(f"Warning: SQLite database not found at {db_path}")

    print("Environment looks good.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
