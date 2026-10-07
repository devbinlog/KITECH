FROM python:3.11-slim

# Install system dependencies required by matplotlib (freetype, libpng, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6 \
    libpng16-16 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy the entire workspace so uv workspace dependency resolution works correctly
COPY . /app

# Sync all workspace packages
RUN uv sync --frozen --all-packages

ENV PYTHONUNBUFFERED=1

EXPOSE 8014

# Run from workspace root so `shared/` is importable as a top-level package
CMD ["uv", "run", "--no-sync", "uvicorn", "src.service:app", \
     "--app-dir", "agents/cell-schedule-visualizer", \
     "--host", "0.0.0.0", "--port", "8014"]
