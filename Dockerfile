FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY api/requirements.txt /tmp/requirements.txt
RUN python -m venv /app/.venv && \
    /app/.venv/bin/pip install -r /tmp/requirements.txt

COPY api /app/api
RUN chmod +x /app/api/scripts/start.sh

CMD ["/app/api/scripts/start.sh"]
