# tests/conftest.py
import importlib
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine, Session

# tests/ está dentro de Pelubot/, así que el root del proyecto es backend/
ROOT = Path(__file__).resolve().parents[1]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

def _import_app_and_deps():
    models = importlib.import_module("app.models")
    db = importlib.import_module("app.db")
    routes = importlib.import_module("app.api.routes")
    main = importlib.import_module("app.main")
    return models, db, routes, main

@pytest.fixture()
def app_client(monkeypatch):
    models, db, routes, main = _import_app_and_deps()

    # Engine de prueba: una sola conexión en memoria para todas las sesiones
    engine = create_engine(
        "sqlite://",  # equivalente a :memory: pero con StaticPool
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Crear todas las tablas del modelo en esta conexión compartida
    SQLModel.metadata.create_all(engine)

    # Dependency override para que la app use nuestra sesión de test
    def get_test_session():
        with Session(engine) as s:
            yield s

    # En tus rutas usas Depends(get_session); aquí lo sobreescribimos
    main.app.dependency_overrides[routes.get_session] = get_test_session

    client = TestClient(main.app)
    try:
        yield client
    finally:
        main.app.dependency_overrides.clear()
