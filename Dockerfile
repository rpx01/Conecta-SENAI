# Estágio 1: Builder - Instala as dependências
FROM python:3.12-slim AS builder

# Define variáveis de ambiente para o Poetry
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Instala o Poetry
RUN pip install poetry

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos de dependência para aproveitar o cache do Docker
COPY pyproject.toml poetry.lock ./

# Instala as dependências do projeto, excluindo as de desenvolvimento
RUN poetry install --no-dev --no-root

# Estágio 2: Runtime - A imagem final que será executada
FROM python:3.12-slim AS runtime

# Define o diretório de trabalho
WORKDIR /app

# Instala o cliente do PostgreSQL para o comando 'pg_isready'
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copia o ambiente Python com as dependências instaladas do estágio 'builder'
COPY --from=builder /usr/local /usr/local

# Copia o código da sua aplicação para o container
COPY . .

# Torna o script de inicialização executável
RUN chmod +x /app/scripts/auto_migrate.sh

# Expõe a porta que sua aplicação usará
EXPOSE 8080

# Define o script de inicialização como o ponto de entrada do container
ENTRYPOINT ["/app/scripts/auto_migrate.sh"]
