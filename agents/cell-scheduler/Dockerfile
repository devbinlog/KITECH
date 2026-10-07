FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy the entire workspace
COPY . /app

RUN uv sync --frozen --all-packages
WORKDIR /app/agents/cell-scheduler

CMD ["uv", "run", "--no-sync", "uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8002"]
