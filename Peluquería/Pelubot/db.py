# db.py
"""
Módulo de configuración y acceso a la base de datos para la aplicación de reservas.
Incluye funciones para inicializar la base y obtener sesiones.
"""
from __future__ import annotations
import os
from sqlmodel import SQLModel, create_engine, Session

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pelubot.db")

# Para SQLite en FastAPI (múltiples hilos)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def create_db_and_tables() -> None:
    """
    Crea las tablas de la base de datos si no existen (idempotente).
    """
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Dependency de FastAPI: abre y cierra la sesión por request.
    Uso:
        with get_session() as session:
            ...
    """
    with Session(engine) as session:
        yield session
