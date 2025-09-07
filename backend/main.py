# main.py
"""
Archivo principal de ejecución del asistente de reservas de peluquería.
Configura la aplicación FastAPI, logging, middleware y ciclo de vida.
"""
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv  # pip install python-dotenv
load_dotenv()  # Cargar .env lo primero

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router
from db import create_db_and_tables
from sqlmodel import Session
from datetime import date, timedelta
from db import engine
from logic import sync_from_gcal_range

# Logging / errores
from core.logging_config import setup_logging
from core.middleware import RequestIDMiddleware
from core.errors import install_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configuración global de logging
    setup_logging()
    # Crear tablas al arrancar
    create_db_and_tables()

    # Auto-sync opcional desde Google Calendar al iniciar
    try:
        if os.getenv("AUTO_SYNC_FROM_GCAL", "false").lower() in ("1","true","yes","si","sí","y"):
            days = int(os.getenv("AUTO_SYNC_FROM_GCAL_DAYS", "7"))
            default_service = os.getenv("DEFAULT_SERVICE_FOR_SYNC", "corte")
            start = date.today()
            end = start + timedelta(days=max(0, days-1))
            with Session(engine) as s:
                sync_from_gcal_range(s, start, end, default_service=default_service, by_professional=True)
    except Exception:
        # No bloquea el arranque si falla
        pass

    yield
    # Aquí podrías cerrar recursos si hiciera falta


def create_app() -> FastAPI:
    app = FastAPI(
        title="PeluBot MVP",
        version="0.6.0",
        description="MVP de peluquería con intents y reservas (persistencia en SQLite) usando FastAPI.",
        lifespan=lifespan,
    )

    # CORS configurable por entorno (ORIGINS=dominio1,dominio2)
    origins_env = os.getenv("ORIGINS")
    if origins_env:
        allow_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
    else:
        allow_origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware para request_id y logs de latencia
    app.add_middleware(RequestIDMiddleware)

    # Handlers globales para errores (formato 'detail' compatible con tests)
    install_exception_handlers(app)

    # Montamos rutas principales
    app.include_router(router)

    return app


app = create_app()
