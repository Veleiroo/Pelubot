# Sincronización BD ↔ Google Calendar

## Modelo
- La base de datos actúa como fuente de verdad.
- Cada reserva almacena `google_event_id` y `google_calendar_id`.

## Idempotencia
- Crear/actualizar eventos usando `reservation.id` como clave.
- Reintentos utilizan el `google_event_id` existente.

## Reconciliación
- Tarea periódica (diaria u horaria) que compara BD y Calendar.
- Los conflictos se registran en logs para revisión manual.

Endpoints administrativos añadidos (protegidos por API key):
- POST `/admin/sync` — Dispara sincronización bajo demanda.
  - Body: `{mode: import|push|both, start?: YYYY-MM-DD, end?: YYYY-MM-DD, days?: number, by_professional?: boolean, calendar_id?: string, professional_id?: string, default_service?: string}`
  - Ej.: `{"mode":"both","days":7}`
- POST `/admin/conflicts` — Detecta conflictos BD ↔ Google Calendar en un rango.
  - Body: `{start?: YYYY-MM-DD, end?: YYYY-MM-DD, days?: number, by_professional?: boolean, calendar_id?: string, professional_id?: string}`
  - Respuesta: contadores y ejemplos de `missing_in_gcal`, `orphaned_in_gcal`, `time_mismatch`, `overlaps_external`.

## Manejo de errores
- Retries con backoff exponencial ante errores 5xx o rate limits.
- Alertas en caso de repetidos fallos.

Notas de entorno:
- `PELUBOT_FAKE_GCAL=1` fuerza cliente simulado (útil en desarrollo sin credenciales).
- `GOOGLE_SERVICE_ACCOUNT_JSON` o `GOOGLE_OAUTH_JSON` deben estar definidos en producción.
