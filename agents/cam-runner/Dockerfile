FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy the entire workspace to resolve local uv dependencies correctly
COPY . /app

RUN uv sync --frozen --all-packages

# Legacy library code uses `from core import ...` (BaseAgent base class).
# `core/` lives under /app/shared/, so we expose it via PYTHONPATH.
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/shared

# Start the cam-runner service on port 8011
WORKDIR /app/agents/cam-runner

EXPOSE 8011

CMD ["uv", "run", "--no-sync", "uvicorn", "src.service:app", "--host", "0.0.0.0", "--port", "8011"]
