#!/bin/bash

# Aguarda o banco de dados ficar pronto.
# Adicione as variáveis DB_HOST, DB_PORT e DB_USER no seu ambiente.
# Exemplo: DB_HOST=db, DB_PORT=5432, DB_USER=user

echo "Aguardando o banco de dados..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -q -U $DB_USER; do
  echo "Banco de dados indisponível - aguardando..."
  sleep 1
done

echo "Banco de dados pronto!"

# Executa as migrações do banco de dados
echo "Executando migrações do banco de dados..."
flask --app src.main db upgrade

# Inicia a aplicação
echo "Iniciando o Gunicorn..."
exec gunicorn --config ./gunicorn.conf.py 'src.main:create_app()'
