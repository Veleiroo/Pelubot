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

## Manejo de errores
- Retries con backoff exponencial ante errores 5xx o rate limits.
- Alertas en caso de repetidos fallos.

