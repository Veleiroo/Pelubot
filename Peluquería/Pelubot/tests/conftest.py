# tests/conftest.py
import importlib.util
from pathlib import Path
from types import ModuleType
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine, Session

# tests/ está dentro de Pelubot/, así que el root del proyecto es el padre directo de tests/
ROOT = Path(__file__).resolve().parents[1]
APP_FILE = ROOT / "main.py"

# 🔧 AÑADIR el directorio del proyecto al sys.path para que 'utils', 'core', etc. se puedan importar
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

def _load_module(name: str, file: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, file)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod

def _import_app_and_deps():
    # Con ROOT ya en sys.path, los imports internos como 'from utils...' funcionarán
    models = _load_module("models", ROOT / "models.py")
    db = _load_module("db", ROOT / "db.py")
    routes = _load_module("routes", ROOT / "routes.py")
    main = _load_module("main", APP_FILE)
    return models, db, routes, main

@pytest.fixture()
def app_client(monkeypatch):
    models, db, routes, main = _import_app_and_deps()

    # ✅ Engine de test: una sola conexión en memoria para TODAS las sesiones
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
