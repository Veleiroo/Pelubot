# Desarrollo y despliegue del Frontend

Este repo soporta dos modos con Docker Compose:

1) Modo dev (Vite) – hot reload en :8080
2) Modo prod (nginx) – build estático en :8080

## Diagnóstico rápido

- `docker compose ps`
- `docker compose logs -f frontend` (prod) o `docker compose logs -f frontend-dev` (dev)
- `docker compose exec frontend sh -lc 'ls -lah /usr/share/nginx/html && head -n5 /usr/share/nginx/html/index.html'`
- `docker compose exec frontend-dev sh -lc 'ls -lah dist || true'` (en dev no hay dist, sirve Vite)

## Modo Dev (Vite en Docker)

Arranca backend + frontend-dev (Vite) mapeado en :8080:

```
make docker-dev
```

Detalles:
- Servicio `frontend-dev` monta `Frontend/shadcn-ui` dentro del contenedor y corre `pnpm dev --host 0.0.0.0`.
- Variables inyectadas: `VITE_API_BASE_URL=http://localhost:8776`, `VITE_API_KEY`.
- Hot reload real. Tras editar `.tsx`, refresca y verás el cambio.

## Modo Prod (nginx con dist)

Fuerza build limpio del frontend y arranca backend + frontend (nginx):

```
make docker-prod
```

Equivalente a:
- `docker compose build --no-cache frontend`
- `docker compose up -d backend frontend`

Comprueba el contenido servido:

```
docker compose exec frontend sh -lc 'ls -lah /usr/share/nginx/html && head -n5 /usr/share/nginx/html/index.html'
```

## Notas

- Usa solo uno a la vez: `frontend` (prod) o `frontend-dev` (dev). Los targets detienen el otro si está en marcha.
- Si cambias variables `VITE_…`, reconstruye prod (`make docker-prod`). En dev basta reiniciar `frontend-dev`.
- El backend corre en `http://localhost:8776`. El dev front habla directo con esa URL.

## Flujo de reserva: estado y stepper

- Estado persistido en `src/store/booking.ts` (zustand):
  - `serviceId`, `professionalId`, `date` (YYYY-MM-DD), `slotStart` (ISO)
  - Acciones: `setService`, `setProfessional`, `setDate`, `setSlot`, `reset`
- Stepper interactivo en `src/components/BookingSteps.tsx`:
  - Basado en ruta actual: `/book/service` → service, `/book/date` → date, `/book/confirm` → confirm
  - Reglas navegación: service siempre; date exige `serviceId`; confirm exige `serviceId` y `slotStart` o `date`.
  - Accesible: `aria-current="step"`, foco visible, navegación con teclado del navegador.
- Restauración de estado:
  - En Service → al seleccionar, se guarda en store y se propaga `?service=<id>` en la URL.
- En Date/Confirm se lee del store y, si falta, se redirige a Service.

## UI (dark + shadcn) — criterios de estilo

- Contenedores centrados con anchos contenidos (`max-w-3xl` para calendario; `max-w-6xl` para grillas de servicio), paddings fluidos (`px-6 sm:px-8`).
- Jerarquía: títulos `text-2xl sm:text-3xl font-bold`, subtítulos `text-sm text-muted-foreground`.
- Secciones en `Card` para agrupar contenido (servicios, calendario, resumen) con borde sutil `border-border/50`, fondo `bg-card/60` y sombra suave.
- Microinteracciones consistentes: botones `variant="ghost"` para acciones neutrales (navegación mes), CTA primario con `bg-emerald-500` y focus visible `focus-visible:ring-emerald-500`.
- Calendario: 7 columnas fijas, celdas `aspect-square` con `tabular-nums`, estados accesibles (disponible/seleccionado/hoy/inactivo) y transición de mes (fade 120ms).
- Stepper: más aire y contraste (estado completado ✓ en verde, actual con anillo, pendiente atenuado), accesible con `aria-current="step"`.

Al añadir pasos/pantallas:
- Reutiliza los mismos contenedores y espaciados (`space-y-6` entre bloques), y la misma paleta.
- Asegura foco visible y feedback deshabilitado en CTAs (`disabled:opacity-50 disabled:pointer-events-none`).
- Mantén grids responsivos (1/2/3 columnas) y tipografía uniforme.
