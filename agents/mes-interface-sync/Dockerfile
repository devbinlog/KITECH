FROM python:3.11-slim

WORKDIR /app/agents/mes-interface-sync

RUN pip install --no-cache-dir asyncpg==0.29.0 PyYAML==6.0.2

COPY config ./config
COPY src ./src

ENV PYTHONPATH=/app/agents/mes-interface-sync/src

ENTRYPOINT ["python", "-m", "mes_interface_sync.main"]
CMD ["run"]
