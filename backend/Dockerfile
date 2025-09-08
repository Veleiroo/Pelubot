FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Europe/Madrid

WORKDIR /app

# Dependencias
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /app/backend/requirements.txt

# Código
COPY backend /app/backend

WORKDIR /app/backend

EXPOSE 8776

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8776", "--workers", "2", "--log-level", "info"]

