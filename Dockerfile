# Estágio 1: Builder - Instala as dependências
FROM python:3.12-slim AS builder

# Define variáveis de ambiente para otimizar a execução
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1

WORKDIR /app

# Instala as ferramentas de build e o Poetry
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir poetry

# Copia TODOS os arquivos do projeto primeiro
# Esta é a principal correção: agora o diretório 'src' estará presente.
COPY . .

# Instala as dependências do projeto, agora com o 'src' disponível
RUN poetry config virtualenvs.create false \
    && poetry install --without dev --no-interaction --no-ansi

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
CMD sh -c "flask --app src.main db upgrade && gunicorn --factory -b 0.0.0.0:${PORT:-8080} src.main:create_app"
