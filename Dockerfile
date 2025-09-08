FROM python:3.12-slim

# Configurações globais
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=on \
    POETRY_VERSION=1.8.3 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# Dependências do sistema + Poetry
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl postgresql-client \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir "poetry==${POETRY_VERSION}"

# 1) Copiar apenas manifestos para maximizar cache
COPY pyproject.toml poetry.lock* ./

# 2) Falhar cedo se o lock estiver inválido (mensagem clara)
#    Se não houver poetry.lock, este comando falha — será regenerado no passo seguinte.
RUN poetry check --lock || true

# 3) Garantir lock compatível com a versão do Poetry e com o pyproject atual
#    --no-update mantém as versões já travadas; se não der, roda 'poetry lock' normal.
RUN (poetry lock --no-update || poetry lock)

# 4) Instalar dependências (sem instalar o pacote do projeto)
RUN poetry install --without dev --no-ansi --no-root

# 5) Copiar código e instalar apenas o pacote do projeto
COPY src ./src
# (copie também outros arquivos necessários ao runtime)
COPY gunicorn.conf.py .
COPY alembic.ini .
COPY migrations ./migrations

# Instala o próprio projeto (modo editável fallback c/ pip)
RUN poetry install --only-root --no-ansi || pip install -e .

# Comando padrão (ajuste se o seu for diferente)
CMD ["gunicorn", "-c", "./gunicorn.conf.py", "src.main:create_app()"]
