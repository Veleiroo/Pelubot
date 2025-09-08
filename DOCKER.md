# Despliegue con Docker

Este repo incluye `docker-compose.yml` para levantar backend y frontend con un solo comando.

## Requisitos
- Docker y Docker Compose. Si tienes el plugin v2, usa `docker compose`. Si solo
  tienes v1, `make docker-up` lo detecta y usará `docker-compose` automáticamente.

## Variables de entorno
Crea un archivo `.env` en la raíz (puedes copiar de `.env.example`) con:

```
API_KEY=changeme
TZ=Europe/Madrid
GOOGLE_OAUTH_JSON=/app/backend/oauth_tokens.json
DATABASE_URL=sqlite:////app/backend/data/pelubot.db
BACKEND_PORT=8776
FRONTEND_PORT=8080
# Para desarrollo sin tocar Google Calendar
# PELUBOT_FAKE_GCAL=1
```

Opcional (si usas Service Account):
```
GOOGLE_SERVICE_ACCOUNT_JSON={...json...}
GOOGLE_IMPERSONATE_EMAIL=usuario@dominio
```

Coloca tu `backend/oauth_tokens.json` en el repo si usas OAuth de usuario (se montará en el contenedor). Si usas Service Account, no es necesario ese archivo.

## Levantar servicios

```
# con plugin v2
docker compose up --build -d
# o con Make (auto-detecta v1/v2)
make docker-up
```

Accesos:
- Backend: http://localhost:8776
- Frontend: http://localhost:8080

El frontend usa `/api` y Nginx proxya al backend dentro de la red de Docker, por lo que no hay problemas de CORS.

### Modo debug de la SPA

Para facilitar el diagnóstico sin herramientas externas, la SPA incluye una ruta `/debug` con utilidades:
- Ver config efectiva (BASE, presencia de API Key enmascarada)
- Probar `/health`, `/ready`, `/services`, `/professionals`
- Consultar `/slots/days` y `/slots` y 
- Lanzar la confirmación con el slot seleccionado

Se activa en build con `VITE_ENABLE_DEBUG=1` (por defecto activado en Compose). Para desactivarlo:

```
FRONT_ENABLE_DEBUG=0 docker compose up --build -d frontend
```

Importante: los endpoints protegidos del backend (crear/cancelar/reprogramar reservas y admin)
requieren API Key. La SPA lee `VITE_API_KEY` en build-time. Puedes suministrarla de dos formas:

- Definiendo `FRONT_API_KEY` en tu `.env` (la `docker-compose.yml` lo pasará como build-arg), o
- Reutilizando la `API_KEY` del backend (por defecto).

Ten en cuenta que en una SPA la API Key queda embebida en los assets estáticos; para producción
valora un backend for frontends o auth diferente.

## Parar y limpiar

```
# con plugin v2
docker compose down -v
# o
make docker-down
```

## Logs

```
# con plugin v2
docker compose logs -f --tail=200
# o
make docker-logs
```

## E2E con Playwright (solo para prueba)

Incluimos un runner de Playwright en `e2e/` para automatizar el flujo de reservas. Genera capturas, vídeos y trazas en `e2e/artifacts/`.

- Levantar y ejecutar pruebas (headless):

```
make e2e
```

- Modo depuración (headed en contenedor con xvfb):

```
make e2e-headed
```

Notas:
- El servicio `e2e` depende de `backend` y `frontend` (usa la red interna y apunta a `http://frontend`).
- Para desinstalar Playwright al finalizar la beta, basta con eliminar la carpeta `e2e/`, el servicio `e2e` de `docker-compose.yml` y los targets del `Makefile`.
