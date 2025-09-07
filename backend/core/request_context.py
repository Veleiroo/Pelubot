import logging
import contextvars

# ContextVar para propagar el request_id durante la request
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

class RequestContextFilter(logging.Filter):
    """
    Inserta request_id en todos los logs (o '-' si no hay).
    """
    def filter(self, record: logging.LogRecord) -> bool:
        rid = request_id_var.get()
        record.request_id = rid if rid else "-"
        return True

