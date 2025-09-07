# utils/date.py
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Madrid")

MAX_AHEAD_DAYS = 183  # ~6 meses (evita dependencias externas)
def now_tz() -> datetime:
    return datetime.now(TZ)

def validate_target_dt(dt: datetime) -> None:
    """
    Reglas:
    - Debe ser "aware" (con tz). Si viene naive, se asume Europe/Madrid.
    - No puede ser pasado.
    - No puede estar más allá de 6 meses (~183 días).
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    _now = now_tz()
    if dt < _now:
        raise ValueError("La fecha/hora está en el pasado.")
    if dt > _now + timedelta(days=MAX_AHEAD_DAYS):
        raise ValueError("La fecha/hora excede el límite de 6 meses.")
