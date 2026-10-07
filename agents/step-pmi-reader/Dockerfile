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

# Copy only the step-pmi-reader agent source (build context is root of repo)
COPY agents/step-pmi-reader/pyproject.toml ./pyproject.toml
COPY agents/step-pmi-reader/src ./src
COPY shared/common ./shared/common

# Install runtime dependencies via pip (pythonocc-core is already installed via conda)
RUN pip install --no-cache-dir \
    "fastapi>=0.100.0" \
    "uvicorn>=0.20.0" \
    "python-multipart>=0.0.9" \
    "python-dotenv>=1.0.0"

EXPOSE 8012

CMD ["uvicorn", "src.service:app", "--host", "0.0.0.0", "--port", "8012"]
