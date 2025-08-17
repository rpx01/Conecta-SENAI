FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Instala o postgresql-client para usar o comando pg_isready
RUN apt-get update && apt-get install -y postgresql-client

WORKDIR /app

# Instalação das dependências (mantenha como estava)
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry && poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

COPY . .

# Expõe a porta (mantenha como estava)
EXPOSE 8080

# Seta o entrypoint para o script (mantenha como estava)
ENTRYPOINT ["/app/scripts/auto_migrate.sh"]

WORKDIR /app

RUN apt-get update && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    pip install poetry

COPY poetry.lock pyproject.toml ./

RUN poetry lock --no-interaction
RUN poetry install --no-root --without dev

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local /usr/local
COPY ./src ./src
COPY ./migrations ./migrations
COPY alembic.ini ./migrations/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8080/ || exit 1

CMD sh -c "flask --app src.main db upgrade && gunicorn --factory -b 0.0.0.0:${PORT:-8080} src.main:create_app"
