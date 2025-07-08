# Usar uma imagem base oficial e slim para menor tamanho
FROM python:3.11-slim

# Definir variáveis de ambiente para Python e Poetry
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_VIRTUALENVS_CREATE=false

# Definir o diretório de trabalho
WORKDIR /app

# Instalar o Poetry
RUN pip install poetry

# Copiar apenas os arquivos de dependência primeiro para aproveitar o cache do Docker
COPY poetry.lock pyproject.toml ./

# Garantir que o arquivo lock esteja sincronizado com o pyproject
RUN poetry lock --no-interaction

# Instalar as dependências de produção
RUN poetry install --no-root --without dev

# Copiar o restante do código-fonte da aplicação
COPY ./src ./src

# Expor a porta que o Gunicorn usará
EXPOSE 8080

# Comando para iniciar a aplicação
CMD ["gunicorn", "src.main:app", "--bind", "0.0.0.0:8080"]
