# Runbook de Operaciones

## Fallo en Google Calendar
1. Revisar logs de `google_calendar.py`.
2. Reintentar la operación manualmente.
3. Si persiste, registrar incidencia y crear la reserva a mano.

## Huecos incoherentes
1. Ejecutar `sync_from_gcal_range` para reconcilio.
2. Comparar con agenda externa y corregir.

## Restaurar copia de seguridad
1. Detener el servicio.
2. Sustituir el archivo de BD por el backup.
3. Reiniciar y verificar integridad.

## Webhooks de mensajería
- Validar que los tokens y secretos están activos.
- Revisar respuestas de la API externa ante fallos.

