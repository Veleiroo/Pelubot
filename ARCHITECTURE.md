# Arquitectura de PeluBot

## Componentes
- **Backend (FastAPI)**
  - Paquete `app/` con submódulos:
    - `api/` (rutas), `services/` (lógica), `integrations/` (Google Calendar), `core/` (logging, middleware, errores), `utils/` (fechas), `db.py`, `models.py`, `data.py`.
  - Exposición REST para catálogo, slots, reservas y endpoints de administración.
- **Frontend (React + Vite + shadcn/ui)**
  - Flujo de reservas y consumo de la API.
- **Base de datos**
  - SQLite en desarrollo; preparado para Postgres.
- **Integraciones externas**
  - Google Calendar para sincronizar reservas.
  - Telegram/WhatsApp como canales opcionales.

## Flujos principales
1. El usuario consulta huecos disponibles (`GET /slots`).
2. La reserva se persiste y crea un evento en Google Calendar.
3. Procesos periódicos reconcilian BD y Calendar.

## Dependencias clave
- Python 3.11+, FastAPI, SQLModel.
- Node 18+, pnpm, React.
