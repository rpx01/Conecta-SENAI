FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=on \
    POETRY_VERSION=1.8.3 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /workspace

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl postgresql-client \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir "poetry==${POETRY_VERSION}"

# Copia apenas os manifestos para aproveitar cache durante a instalação
COPY pyproject.toml ./
COPY packages/common/pyproject.toml packages/common/pyproject.toml
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/api/poetry.lock apps/api/poetry.lock

# Copia o código dos pacotes locais necessários para resolver dependências
COPY packages/common/conectasenai_common packages/common/conectasenai_common

WORKDIR /workspace/apps/api

RUN poetry check --lock || true
RUN (poetry lock --no-update || poetry lock)
RUN poetry install --without dev --no-ansi --no-root

# Copia o restante do código do aplicativo
COPY apps/api/src src
COPY apps/api/migrations migrations
COPY apps/api/gunicorn.conf.py .
COPY apps/api/alembic.ini .
COPY apps/api/start.sh .
RUN chmod +x start.sh

# Copia novamente o pacote compartilhado para garantir que alterações sejam refletidas
COPY packages/common ../../packages/common

RUN poetry install --only-root --no-ansi || pip install -e .

CMD ["./start.sh"]
