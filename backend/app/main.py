"""
App entrypoint for PeluBot backend (FastAPI). Structured package version.
"""
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Use API router from the structured package (it re-exports legacy routes)
from app.api.routes import router

from app.db import create_db_and_tables
from sqlmodel import Session
from datetime import date, timedelta
from app.db import engine
from app.services.logic import sync_from_gcal_range

from app.core.logging_config import setup_logging
from app.core.middleware import RequestIDMiddleware
from app.core.errors import install_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    create_db_and_tables()

    try:
        if os.getenv("AUTO_SYNC_FROM_GCAL", "false").lower() in ("1","true","yes","si","sí","y"):
            days = int(os.getenv("AUTO_SYNC_FROM_GCAL_DAYS", "7"))
            default_service = os.getenv("DEFAULT_SERVICE_FOR_SYNC", "corte")
            start = date.today()
            end = start + timedelta(days=max(0, days-1))
            with Session(engine) as s:
                sync_from_gcal_range(s, start, end, default_service=default_service, by_professional=True)
    except Exception:
        pass

    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="PeluBot MVP",
        version="0.6.0",
        description="MVP de peluquería con intents y reservas (persistencia en SQLite) usando FastAPI.",
        lifespan=lifespan,
    )

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

    app.add_middleware(RequestIDMiddleware)
    install_exception_handlers(app)
    app.include_router(router)
    return app


app = create_app()
