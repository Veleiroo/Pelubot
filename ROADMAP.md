# Roadmap / Backlog

Este documento recoge mejoras y próximos pasos para el proyecto.

## Backend (prioridad alta)
- Dockerización: añadir `Dockerfile` y `docker-compose.yml` con variables de entorno y volumen para SQLite.
- Métricas: exponer `/metrics` (Prometheus) e instrumentar FastAPI.
- Rate limiting: limitar endpoints críticos (crear/cancelar/reprogramar) por API key/IP.
- Migraciones: incorporar Alembic para evolución de `ReservationDB`.
- Tareas programadas: cron o scheduler (APScheduler) para reconciliar `admin/sync`.
- Hardening de configuración: validaciones de env (`pydantic-settings`) y secreto de API gestionado por vault.
- Observabilidad: logs en JSON opcional y trazas (OpenTelemetry) si procede.
- Alertas: notificar fallos repetidos de sincronización.

## Backend (mejoras de DX)
- Makefile `prod` (uvicorn con workers y logging rotativo).
- Scripts CLI (click/typer) para operaciones comunes: clear, sync, conflicts.
- Tests adicionales: pruebas sobre conflictos y reconciliación en escenarios límite.

## Google Calendar
- Soporte “dry-run” en `/admin/sync` para ver cambios sin aplicar.
- Etiquetado de eventos con colores por tipo de servicio.
- Opcional: sincronización de descripciones/notas del cliente.

## Frontend (próximos pasos)
- Config de entorno: base URL del backend por `import.meta.env` y `.env` de Vite.
- Manejo de errores de API unificado (toasts y estados vacíos).
- Validaciones de formularios (fechas/horas, profesional/servicio).
- Estado de carga y accesibilidad en los componentes de reserva.
- Pruebas E2E básicas (Playwright) para el flujo de reserva.
- Limpieza de assets y estructura (si procede) y scripts de build/previews.

