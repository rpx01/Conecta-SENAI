# Conecta_SENAI
Agenda de laboratórios e salas do SENAI

[![CI](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml/badge.svg)](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml)

## Changelog
Consulte o arquivo [CHANGELOG.md](CHANGELOG.md) para detalhes das versões.

## Configuração rápida

1. Instale as dependências do projeto usando o Poetry:

   ```bash
   poetry install
   ```

2. Copie o arquivo `.env.example` para `.env` e ajuste as variáveis de ambiente:

   ```bash
   cp .env.example .env
   # edite o arquivo .env com seus dados
   ```
Todas as variáveis disponíveis estão listadas em `.env.example`.

   A aplicação também reconhece a variável `FLASK_SECRET_KEY`. Uma das duas deve estar definida; se nenhuma estiver presente, a aplicação aborta a inicialização. Use um valor longo e aleatório (por exemplo, `export SECRET_KEY=$(openssl rand -hex 32)`).

   Se `DATABASE_URL` não for informado ou estiver vazio, o sistema utiliza por padrão um banco SQLite local (`agenda_laboratorio.db`).

   Um servidor Redis precisa estar ativo no endereço definido em `REDIS_URL` para que a limitação de requisições e a revogação de tokens funcionem corretamente.

3. Execute as migrações do banco para criar as tabelas necessárias:

   ```bash
   flask --app src.main db upgrade
   ```

4. Execute a suíte de testes para verificar se tudo está funcionando:

   ```bash
   pytest
   ```

5. Para iniciar a aplicação em modo de desenvolvimento, execute:

   ```bash
   flask --app src.main run
   ```

   As tabelas do banco estarão disponíveis após rodar as migrações. O usuário
   administrador será criado automaticamente apenas se `ADMIN_EMAIL` e
   `ADMIN_PASSWORD` estiverem definidos.

6. As rotas de autenticação e cadastro possuem uma limitação de
   requisições por minuto para evitar abusos de login ou criação de contas.

## Usando Docker

Uma alternativa é rodar a aplicação em um container Docker. Para construir a imagem execute:

   ```bash
docker build -t agenda-senai .
```

Em seguida, inicie o container usando as variáveis definidas em um arquivo `.env`:

   ```bash
docker run -p 8000:8000 --env-file .env agenda-senai
```

A aplicação ficará disponível em [http://localhost:8000](http://localhost:8000).

## Estrutura do Projeto

- `src/` - Código-fonte da aplicação Flask.
- `src/routes/` - Blueprints com as rotas REST de cada recurso.
- `src/models/` - Definições das tabelas e regras de negócios.
- `src/static/` - Arquivos estáticos de frontend (HTML, CSS e JavaScript).
- `migrations/` - Migrações do banco de dados gerenciadas pelo Flask-Migrate.
- `tests/` - Casos de teste automatizados.

## Principais Endpoints da API

| Método | Endpoint | Descrição |
| ------ | -------- | --------- |
| `POST` | `/api/login` | Autenticação de usuários |
| `POST` | `/api/usuarios` | Criação de usuário |
| `GET` | `/api/usuarios` | Listagem de usuários |
| `POST` | `/api/salas` | Criação de sala |
| `GET` | `/api/salas/<id>` | Detalhes de uma sala |
| `POST` | `/api/ocupacoes` | Criação de ocupação de sala |
| `GET` | `/api/ocupacoes` | Consulta de ocupações |
| `DELETE` | `/api/ocupacoes/<id>` | Remoção de ocupação |

## Integração Contínua

Este repositório possui um fluxo de integração contínua configurado no GitHub
Actions. O workflow `.github/workflows/ci.yml` instala as dependências do
projeto e executa o `flake8`, o `bandit` e a suíte de testes com `pytest` a
cada push ou pull request para a branch `main`.

