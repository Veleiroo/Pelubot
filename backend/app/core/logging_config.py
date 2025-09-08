import logging
import logging.config

def setup_logging():
    """
    Configura logging estructurado con un filtro que añade request_id.
    """
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": "%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s"}
        },
        "filters": {"request_context": {"()": "app.core.request_context.RequestContextFilter"}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "filters": ["request_context"],
            }
        },
        "root": {"level": "INFO", "handlers": ["console"]},
        "loggers": {
            "uvicorn": {"level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"level": "WARNING"},
            "fastapi": {"level": "INFO"},
            "httpx": {"level": "WARNING"},
        },
    })
