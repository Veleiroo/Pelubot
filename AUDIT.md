# Auditoría de PeluBot

## Hallazgos

### Críticos
- La base de datos se creaba en la raíz del repositorio por una ruta relativa.
- No existe idempotencia ni reconciliación formal con Google Calendar.
- Falta documentación de arquitectura y despliegue.

### Altos
- Comentarios con emojis y estilo inconsistente.
- Formularios del frontend sin validaciones mínimas.

### Medios
- Ausencia de runbook y guía operativa.

### Bajos
- Presencia de código y archivos generados que no deberían versionarse.

## Riesgos, impacto y mitigación
- **Rutas de BD no controladas:** generan archivos accidentales y dificultan el despliegue. *Mitigación:* usar `DATABASE_URL` y ruta `data/`.
- **Desincronización con Calendar:** puede provocar reservas duplicadas. *Mitigación:* idempotencia por `reservation_id` y reconciliación periódica.

## Quick wins
- Mover la base de datos a un directorio `data/` ignorado por git.
- Eliminar emojis de comentarios y normalizar estilo.
- Añadir documentación de despliegue y operaciones básicas.

## Propuestas estructurales
- Introducir migraciones con Alembic y backups programados.
- Diseñar colas de sincronización con reintentos y backoff.
- Añadir tests de extremo a extremo para frontend y backend.

