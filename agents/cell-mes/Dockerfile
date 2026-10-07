FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy the entire workspace to resolve local uv dependencies correctly
COPY . /app

WORKDIR /app
RUN uv sync --frozen --all-packages

# Start the service
WORKDIR /app/agents/cell-mes

# Run migrations then start the server
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && uv run --no-sync uvicorn src.app.main:app --host 0.0.0.0 --port 8000"]
