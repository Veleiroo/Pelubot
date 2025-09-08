import time
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.core.request_context import request_id_var

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    - Genera X-Request-ID si no viene.
    - Mide latencia y la loguea con método, path y status.
    - Propaga el request_id por ContextVar (para que aparezca en todos los logs).
    """
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request_id_var.set(rid)
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "Unhandled error",
                extra={
                    "method": request.method,
                    "path": str(request.url.path),
                    "latency_ms": int(latency_ms),
                },
            )
            raise
        latency_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = rid
        logger.info("HTTP %s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, latency_ms)
        return response
