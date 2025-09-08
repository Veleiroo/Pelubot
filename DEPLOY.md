# Guía de Despliegue

## Requisitos
- Python 3.11
- Node 18 y `pnpm`

## Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Arranque de desarrollo
uvicorn app.main:app --host 127.0.0.1 --port 8776

# Makefile (recomendado)
make dev-start PORT=8776 FAKE=0
```

## Frontend
```bash
cd Frontend/shadcn-ui
pnpm install
pnpm build
```

## Variables de entorno
- `DATABASE_URL`
- `API_KEY`
- `GCAL_CALENDAR_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON` (ruta o JSON) o `GOOGLE_OAUTH_JSON` (ruta o JSON)
- `GOOGLE_IMPERSONATE_EMAIL` (opcional para Service Account)
- `USE_GCAL_BUSY` (true/false)
- `TZ` (por defecto Europe/Madrid)
- `TELEGRAM_BOT_TOKEN` (opcional)

## Entornos
- **Desarrollo:** SQLite local (`app/data/pelubot.db`), CORS abierto.
- **Producción:** Base de datos gestionada, CORS restringido y secrets en variables.

## Operaciones
- Sincronizar: `POST /admin/sync` (import|push|both)
- Conflictos: `POST /admin/conflicts`
- Limpiar calendarios: `POST /admin/clear_calendars`

Makefile wrappers:
- `make sync-import START=YYYY-MM-DD DAYS=7`
- `make sync-push START=YYYY-MM-DD DAYS=7`
- `make conflicts START=YYYY-MM-DD END=YYYY-MM-DD`
