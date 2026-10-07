FROM python:3.11-slim

WORKDIR /app

# Copy shared common library
COPY shared/common ./shared/common
COPY shared/__init__.py ./shared/__init__.py

# Copy agent source
COPY agents/monitoring-data-replayer/pyproject.toml ./pyproject.toml
COPY agents/monitoring-data-replayer/src ./src

# Install runtime dependencies
RUN pip install --no-cache-dir \
    "fastapi>=0.100.0" \
    "uvicorn[standard]>=0.20.0" \
    "pydantic>=2.0" \
    "nptdms>=1.7.0" \
    "pandas>=2.0.0" \
    "websockets>=12.0" \
    "aiofiles>=23.0"

EXPOSE 8013

CMD ["uvicorn", "src.service:app", "--host", "0.0.0.0", "--port", "8013"]
