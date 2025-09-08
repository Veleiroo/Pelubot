from __future__ import annotations
from typing import List, Dict
from datetime import time
from app.models import Service, Professional

# Servicios disponibles
SERVICES: List[Service] = [
    Service(id="corte", name="Corte de pelo", duration_min=30, price_eur=15.0),
    Service(id="tinte", name="Tinte", duration_min=90, price_eur=45.0),
    Service(id="barba", name="Arreglo de barba", duration_min=20, price_eur=10.0),
]

# Profesionales y servicios que prestan
PROS: List[Professional] = [
    Professional(id="ana", name="Ana", services=["corte", "tinte"]),
    Professional(id="luis", name="Luis", services=["corte", "barba"]),
]

# Índices rápidos
SERVICE_BY_ID: Dict[str, Service] = {s.id: s for s in SERVICES}
PRO_BY_ID: Dict[str, Professional] = {p.id: p for p in PROS}

# Horario semanal
WEEKLY_SCHEDULE = {
    0: [(time(10, 0), time(14, 0)), (time(16, 0), time(20, 0))],
    1: [(time(10, 0), time(14, 0)), (time(16, 0), time(20, 0))],
    2: [(time(10, 0), time(14, 0)), (time(16, 0), time(20, 0))],
    3: [(time(10, 0), time(14, 0)), (time(16, 0), time(20, 0))],
    4: [(time(10, 0), time(14, 0)), (time(16, 0), time(20, 0))],
    5: [(time(10, 0), time(14, 0))],
    6: [],
}

# Mapa profesional → calendario (IDs reales)
PRO_CALENDAR: Dict[str, str] = {
    "ana":  "8c0608d1b29961a8fa08221739a09adcfcef8da54cd5045b8eb68c020a882051@group.calendar.google.com",
    "luis": "988f3f3dcfed070004cceb7e67f0556677ae60a7b98637e965046467585d5edd@group.calendar.google.com",
}

# Uso de busy de GCAL por profesional
PRO_USE_GCAL_BUSY: Dict[str, bool] = {"ana": True, "luis": False}
