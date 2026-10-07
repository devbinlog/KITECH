FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy the entire workspace so uv workspace dependency resolution works correctly
COPY . /app

# Sync all workspace packages (installs torus-mock + shared + fastapi/uvicorn)
RUN uv sync --frozen --all-packages

ENV PYTHONUNBUFFERED=1

EXPOSE 8015

# Run from workspace root so `shared/` is importable as a top-level package
CMD ["uv", "run", "--no-sync", "uvicorn", "src.service:app", \
     "--app-dir", "agents/torus-mock", \
     "--host", "0.0.0.0", "--port", "8015"]
