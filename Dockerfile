# Estágio 1: Builder - Instala as dependências
FROM python:3.12-slim AS builder

# Define variáveis de ambiente para otimizar a execução e configurar o Poetry
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# Instala as ferramentas de build e o Poetry
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "poetry==${POETRY_VERSION}"

# Copia os arquivos de configuração do projeto
COPY pyproject.toml poetry.lock* ./

# RUN poetry lock --no-update  # Use para atualizar o poetry.lock sem alterar as dependências

# Instala as dependências sem o código do projeto
RUN poetry install --without dev --no-ansi --no-root

# Copia o código fonte
COPY src ./src

# Instala somente o pacote do projeto
RUN poetry install --only-root --no-ansi || pip install -e .

# Copia arquivos adicionais necessários em runtime
COPY alembic.ini ./
COPY migrations ./migrations

# Estágio 2: Runtime - Cria a imagem final e mais leve
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala pacotes necessários para a execução em produção
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos e dependências do estágio 'builder'
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Expõe a porta que a aplicação usará
EXPOSE 8080

# Comando para verificar a saúde da aplicação
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8080/ || exit 1

# Comando para iniciar a aplicação
# Executa as migrações do banco de dados e inicia o servidor Gunicorn
CMD ["/bin/bash", "-lc", "SCHEDULER_ENABLED=0 flask --app src.main db upgrade && exec gunicorn 'src.main:create_app()' --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 1 --max-requests 200 --max-requests-jitter 50 --timeout 30 --graceful-timeout 30 --keep-alive 2 --log-level info"]
