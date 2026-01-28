FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY api/requirements.txt /tmp/requirements.txt
RUN python -m venv /app/.venv && \
    /app/.venv/bin/pip install -r /tmp/requirements.txt

COPY api /app/api

CMD ["sh", "-c", "/app/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
