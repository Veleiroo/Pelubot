# data.py
"""
Datos simulados y estructuras principales para la aplicación de reservas de peluquería.
Incluye servicios, profesionales, horarios y mapeo de calendarios.
"""
from __future__ import annotations
from typing import List, Dict, Any
from datetime import time
from models import Service, Professional

# Lista de servicios disponibles en la peluquería
SERVICES: List[Service] = [
    Service(id="corte", name="Corte de pelo", duration_min=30, price_eur=15.0),
    Service(id="tinte", name="Tinte", duration_min=90, price_eur=45.0),
    Service(id="barba", name="Arreglo de barba", duration_min=20, price_eur=10.0),
]

# Lista de profesionales y los servicios que ofrecen
PROS: List[Professional] = [
    Professional(id="ana", name="Ana", services=["corte", "tinte"]),
    Professional(id="luis", name="Luis", services=["corte", "barba"]),
]

# Diccionarios para acceso rápido por ID
SERVICE_BY_ID: Dict[str, Service] = {s.id: s for s in SERVICES}  # Mapeo de servicios por ID
PRO_BY_ID: Dict[str, Professional] = {p.id: p for p in PROS}     # Mapeo de profesionales por ID

# Horarios semanales simulados
# Lunes a viernes: 10-14 y 16-20
# Sábado: 10-14
# Domingo: cerrado
WEEKLY_SCHEDULE = {
    0: [(time(10, 0), time(14, 0)), (time(16, 0), time(20, 0))],  # Lunes
    1: [(time(10, 0), time(14, 0)), (time(16, 0), time(20, 0))],  # Martes
    2: [(time(10, 0), time(14, 0)), (time(16, 0), time(20, 0))],  # Miércoles
    3: [(time(10, 0), time(14, 0)), (time(16, 0), time(20, 0))],  # Jueves
    4: [(time(10, 0), time(14, 0)), (time(16, 0), time(20, 0))],  # Viernes
    5: [(time(10, 0), time(14, 0))],                              # Sábado
    6: [],                                                        # Domingo
}

# Mapa profesional → calendar_id (apuntando a los IDs reales)
PRO_CALENDAR: Dict[str, str] = {
    "ana":  "8c0608d1b29961a8fa08221739a09adcfcef8da54cd5045b8eb68c020a882051@group.calendar.google.com",
    "luis": "988f3f3dcfed070004cceb7e67f0556677ae60a7b98637e965046467585d5edd@group.calendar.google.com",
}

# Control por profesional del uso de GCAL busy (True=aplicar busy; False=ignorar busy)
PRO_USE_GCAL_BUSY: Dict[str, bool] = {
    "ana": True,
    "luis": False,  # desactivado para evitar bloqueo total por eventos de turno
}
