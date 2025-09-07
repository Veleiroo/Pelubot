# Ready for Production Checklist

## Base de datos
- [ ] `DATABASE_URL` configurada para cada entorno.
- [ ] Migraciones con Alembic.
- [ ] Backups automáticos y verificados.

## API
- [ ] Autenticación por API key u OAuth.
- [ ] Validación de entrada y tests.
- [ ] Health/ready endpoints.

## Seguridad
- [ ] Variables de entorno gestionadas como secretos.
- [ ] CORS restringido a dominios conocidos.
- [ ] Dependencias actualizadas.

## Observabilidad
- [ ] Logs estructurados con `request_id`.
- [ ] Métricas y alertas básicas.

## CI/CD
- [ ] Tests automáticos en cada PR.
- [ ] Build del frontend y backend.
- [ ] Escaneo de seguridad.

## Backups
- [ ] Política de retención documentada.
- [ ] Restauraciones probadas regularmente.

## Infraestructura
- [ ] Contenedores con recursos definidos.
- [ ] Monitorización y auto-restart.

