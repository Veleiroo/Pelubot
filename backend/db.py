# db.py
"""
Módulo de configuración y acceso a la base de datos para la aplicación de reservas.
Incluye funciones para inicializar la base y obtener sesiones.
"""
from __future__ import annotations
import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session

# Configuración de la base de datos
# La ruta por defecto coloca el archivo en ``data/pelubot.db``
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "pelubot.db"
DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

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
