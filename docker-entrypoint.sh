#!/bin/sh

# Exporta a variável de ambiente para que o comando flask funcione
export FLASK_APP=src/main.py

echo "Applying database migrations..."
# Aplica as migrações do banco de dados
flask db upgrade

echo "Starting Gunicorn server..."
# Inicia o servidor da aplicação
exec gunicorn --bind 0.0.0.0:8080 "src.main:app"
