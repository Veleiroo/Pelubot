# Guía de Despliegue

## Requisitos
- Python 3.11
- Node 18 y `pnpm`

## Backend
```bash
cd Peluquería/Pelubot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app
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
- `TELEGRAM_BOT_TOKEN`

## Entornos
- **Desarrollo:** SQLite local (`data/pelubot.db`), CORS abierto.
- **Producción:** Base de datos gestionada, CORS restringido y secrets en variables.

