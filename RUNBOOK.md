# Runbook de Operaciones

## Fallo en Google Calendar
1. Revisar logs del backend (`backend/server2.log`).
2. Verificar credenciales (`GOOGLE_SERVICE_ACCOUNT_JSON` o `GOOGLE_OAUTH_JSON`).
3. Probar `/ready` para ver detalle del error.
4. Reintentar sincronización con `POST /admin/sync` (import|push).

## Huecos incoherentes
1. Ejecutar `POST /admin/conflicts` para detectar discrepancias.
2. Ejecutar `POST /admin/sync` en modo `both` para reconciliar.
3. Si persisten, revisar eventos manualmente en GCal.

## Restaurar copia de seguridad (SQLite)
1. Detener el servicio.
2. Sustituir el archivo de BD por el backup (`backend/app/data/*.db`).
3. Reiniciar y verificar integridad.

## Webhooks de mensajería
- Validar que los tokens y secretos están activos.
- Revisar respuestas de la API externa ante fallos.
## Utilidades Makefile
- `make dev-start PORT=8776 FAKE=0` — arranca backend
- `make dev-clear` — borra eventos de GCal (requiere API_KEY)
- `make dev-demo` — flujo de demo end-to-end
- `make conflicts` — detecta conflictos en un rango

## Frontend (desarrollo)
- Variables en `Frontend/shadcn-ui/.env`:
  - `VITE_API_BASE_URL=http://127.0.0.1:8776` (o `/api` si usas nginx)
  - `VITE_API_KEY` debe coincidir con `API_KEY` del backend, salvo que `ALLOW_LOCAL_NO_AUTH=true` en `backend/.env`.
- Arranca: `make dev-start` y en otra terminal `make front-dev`.
