import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

def install_exception_handlers(app: FastAPI):
    """
    Handlers globales coherentes y compatibles con los tests:
    - HTTPException -> {"detail": "..."}
    - ValidationError (422) -> {"detail": [...]}
    - Exception (500) -> {"detail": "..."}
    """
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # Mantiene el log existente
        logger.warning("HTTPException %s: %s", exc.status_code, exc.detail)
        # Formato que esperan los tests de FastAPI: clave 'detail'
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Formato por defecto de FastAPI: lista de errores en 'detail'
        logger.info("Validation error: %s", exc.errors())
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception")
        # Respuesta simple y estándar para 500
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )
