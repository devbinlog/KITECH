FROM mambaorg/micromamba:1.5.8

ENV MAMBA_DOCKERFILE_ACTIVATE=1

USER root

# Install conda-forge packages: Python 3.11 + pythonocc-core + pip
RUN micromamba install -y -n base -c conda-forge \
    python=3.11 \
    pythonocc-core \
    pip \
    && micromamba clean --all --yes

WORKDIR /app

# Copy only the dtp agent source (build context is the root of the repo)
COPY agents/digital-thread-project-manager/pyproject.toml ./pyproject.toml
COPY agents/digital-thread-project-manager/src ./src

# Install runtime dependencies directly (avoid uv workspace resolution issues)
RUN pip install --no-cache-dir \
    "xsdata>=24.0" \
    "xmltodict>=0.13.0" \
    "pyyaml>=6.0" \
    "fastapi>=0.100.0" \
    "uvicorn>=0.20.0" \
    "motor>=3.3.0" \
    "requests>=2.31.0" \
    "python-dotenv>=1.0.0" \
    "fastapi-mcp"

EXPOSE 8205

CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8205"]
