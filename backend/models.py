# models.py
"""
Modelos principales de datos para la API de reservas de peluquería.
Incluye servicios, profesionales, reservas y estructuras de consulta.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime, date, timezone
from sqlmodel import SQLModel, Field as SQLField
from sqlalchemy.types import DateTime  # Import correcto para SQLModel
# Validación de fechas (utilidad)
from utils.date import validate_target_dt, TZ  # TZ = ZoneInfo("Europe/Madrid")

# -----------------------------
# Modelos de datos principales (Pydantic para la API)
# -----------------------------
class Service(BaseModel):
    """Servicio ofrecido (ej.: corte, coloración)."""
    id: str
    name: str
    duration_min: int
    price_eur: float

class Professional(BaseModel):
    """Profesional (ej.: estilista, barbero)."""
    id: str
    name: str
    services: List[str]

class Reservation(BaseModel):
    """Reserva realizada por un cliente."""
    id: str
    service_id: str
    professional_id: str
    start: datetime
    end: datetime
    google_event_id: Optional[str] = None
    google_calendar_id: Optional[str] = None

class SlotsQuery(BaseModel):
    """Consulta de huecos disponibles."""
    service_id: str
    date_str: str
    professional_id: Optional[str] = None
    use_gcal: Optional[bool] = None

class SlotsOut(BaseModel):
    """Respuesta con huecos disponibles."""
    service_id: str
    date: date
    professional_id: Optional[str]
    slots: List[str]

class CancelReservationIn(BaseModel):
    """Solicitud de cancelación de reserva."""
    reservation_id: str = Field(..., json_schema_extra={"example": "res_1"})
class ActionResult(BaseModel):
    """Resultado genérico de acción."""
    ok: bool
    message: str

class RescheduleIn(BaseModel):
    """Solicitud de reprogramación de reserva."""
    reservation_id: str = Field(..., json_schema_extra={"example": "res_1"})
    # Modo clásico: especificar fecha y hora nuevas por separado (compatibilidad)
    new_date: Optional[str] = Field(None, json_schema_extra={"example": "2025-09-06"})
    new_time: Optional[str] = Field(None, json_schema_extra={"example": "18:30"})
    # Modo alternativo: una marca temporal ISO (p. ej. devuelta por /slots)
    # Este campo es opcional y, si está presente, tiene prioridad sobre (new_date,new_time).
    new_start: Optional[str] = Field(
        None,
        json_schema_extra={"example": "2025-09-06T18:30:00+02:00"}
    )
    professional_id: Optional[str] = Field(None, json_schema_extra={"example": "ana"})
class RescheduleOut(BaseModel):
    """Respuesta de reprogramación."""
    ok: bool
    message: str
    reservation_id: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None

class ReservationIn(BaseModel):
    """Entrada para crear reserva (end es opcional; se calcula en backend)."""
    service_id: str
    professional_id: str
    start: datetime
    end: Optional[datetime] = None  # <- ahora opcional

    @field_validator("start")
    @classmethod
    def _validate_start(cls, v: datetime):
        # Fuerza TZ Madrid si viene naive + valida rango (no pasado / <= 6 meses)
        if v.tzinfo is None:
            v = v.replace(tzinfo=TZ)
        validate_target_dt(v)
        return v

# -----------------------------
# Persistencia (SQLModel)
# -----------------------------

class ReservationDB(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: str = SQLField(primary_key=True)
    service_id: str = SQLField()
    professional_id: str = SQLField()
    start: datetime = SQLField(sa_type=DateTime(timezone=True))
    end: datetime = SQLField(sa_type=DateTime(timezone=True))
    google_event_id: Optional[str] = SQLField(default=None, nullable=True)
    google_calendar_id: Optional[str] = SQLField(default=None, nullable=True)
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
    updated_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
