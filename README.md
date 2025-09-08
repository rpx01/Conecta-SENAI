# Conecta_SENAI
Agenda de laboratórios e salas do SENAI

[![CI](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml/badge.svg)](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml)

## Changelog
Consulte o arquivo [CHANGELOG.md](CHANGELOG.md) para detalhes das versões.

## Design System
As diretrizes de estilo do projeto estão descritas em [docs/design-system.md](docs/design-system.md).
Atualize esse documento sempre que novos componentes visuais forem adicionados.

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

   Para envio via Outlook/Office 365, habilite **SMTP AUTH** na conta.
   Caso a conta use MFA, gere uma **senha de aplicativo** ou utilize OAuth
   conforme a política da organização.

   Substitua todos os placeholders `<definir_em_producao>` por valores reais antes do deploy.

   A aplicação também reconhece a variável `FLASK_SECRET_KEY`. Uma das duas deve estar definida; se nenhuma estiver presente, a aplicação aborta a inicialização. Use um valor longo e aleatório (por exemplo, `export SECRET_KEY=$(openssl rand -hex 32)`).

   Se `DATABASE_URL` não for informado ou estiver vazio, o sistema utiliza por padrão um banco SQLite local (`agenda_laboratorio.db`).

   Um servidor Redis precisa estar ativo no endereço definido em `REDIS_URL` para que a limitação de requisições e a revogação de tokens funcionem corretamente.

3. Execute as migrações do banco para criar as tabelas necessárias ou
   atualizar o esquema após mudanças no código. O diretório `migrations`
   será criado automaticamente caso ainda não exista:

   ```bash
   flask --app src.main db upgrade
   ```

   Sempre que atualizar o projeto, rode novamente este comando para
   garantir que novas colunas (como `descricao` em `rateio_configs`)
   estejam presentes no banco de dados.

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

   As rotas de autenticação utilizam cookies com `Secure` e `SameSite=Strict`.
   Em produção, a aplicação deve ser servida via **HTTPS** para que esses
   cookies sejam aceitos pelos navegadores. Para testes locais sem HTTPS, é
   possível definir `COOKIE_SECURE=False` e `COOKIE_SAMESITE=Lax` no arquivo
   `.env`.

6. As rotas de autenticação e cadastro possuem uma limitação de
   requisições por minuto para evitar abusos de login ou criação de contas.

7. Um scheduler baseado em APScheduler gera periodicamente lembretes de
   agendamentos. O intervalo em minutos pode ser ajustado pela variável de
   ambiente `NOTIFICACAO_INTERVALO_MINUTOS` (padrão: `60`). Defina
   `SCHEDULER_ENABLED=0` para desativá-lo completamente.

## Segurança

- **JWT**: A API utiliza tokens JWT para autenticação. Tokens de acesso possuem
  curta duração e tokens de refresh podem ser revogados a qualquer momento.
- **Rate Limiting**: Rotas sensíveis como login e criação de usuários são
  protegidas por limitação de requisições via Flask-Limiter para mitigar
  ataques de força bruta.
- **Credenciais padrão**: Defina valores seguros para `ADMIN_EMAIL`,
  `ADMIN_PASSWORD` e `SECRET_KEY` antes de iniciar a aplicação. Não utilize os
  valores de exemplo em ambientes de produção.

## Política de Segredos

- O recurso de [secret scanning](https://docs.github.com/code-security/secret-scanning/about-secret-scanning)
  do GitHub está habilitado para alertar sobre exposições acidentais de credenciais.
- Nunca versione senhas, tokens ou chaves privadas. Utilize variáveis de ambiente
  e os **GitHub Secrets** nos pipelines.
- Se um segredo for exposto, revogue-o e gere um novo imediatamente, atualizando
  as referências necessárias.

## Usando Docker

Uma alternativa é rodar a aplicação em um container Docker. Para construir a imagem execute:

   ```bash
docker build -t agenda-senai .
```

As migrações não são mais distribuídas no repositório. O diretório será criado
automaticamente quando a aplicação rodar o comando de upgrade. O Dockerfile já
executa `flask db upgrade` antes de iniciar o Gunicorn, garantindo que o banco
esteja sempre na versão correta.

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
- `migrations/` - Criado automaticamente em tempo de execução para armazenar as
  migrações do banco de dados.
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

## Auditoria de dependências

Para verificar vulnerabilidades nas dependências localmente, utilize o
[`pip-audit`](https://pypi.org/project/pip-audit/):

```bash
pip install pip-audit
pip-audit --progress-spinner off
```

O comando acima analisa o ambiente atual e retorna código de saída diferente de
zero se encontrar vulnerabilidades de severidade alta ou crítica.


## Migrações automáticas

Para evitar divergências entre os modelos do SQLAlchemy e o esquema do banco de dados, o repositório disponibiliza o script `scripts/auto_migrate.sh`. Ele gera e aplica migrations de forma automática.

Execute o script sempre que alterar arquivos em `src/models/`:

```bash
./scripts/auto_migrate.sh "Mensagem da migration"
```

Ele realiza três etapas:

1. Garante que o banco esteja atualizado com `flask db upgrade`.
2. Roda `flask db migrate` com autogeração para criar uma nova migration se mudanças forem detectadas.
3. Aplica a nova migration com `flask db upgrade`.

Um workflow opcional (`.github/workflows/migrations.yml`) executa o mesmo processo em PRs e falha caso existam migrations não versionadas. Assim, ao abrir um PR, verifique se novas migrations foram geradas e commitadas.

### Passo a passo para rodar as migrations

1. Certifique-se de que a variável `DATABASE_URL` está configurada no arquivo `.env`.
2. Aplique as migrations pendentes executando:

```bash
flask --app src.main db upgrade
```

3. Caso tenha alterado algum modelo, gere uma nova migration automática e aplique-a:

```bash
flask --app src.main db migrate -m "Descricao da mudança"
flask --app src.main db upgrade
```

Você também pode usar o script que já realiza essas etapas de uma vez:

```bash
./scripts/auto_migrate.sh "Descricao da mudança"
```

### Checklist após alterar modelos

- [ ] Atualize ou crie os arquivos em `src/models/`.
- [ ] Rode `./scripts/auto_migrate.sh "Descrição"` para gerar e aplicar a migration.
- [ ] Inclua os arquivos de migration em `migrations/versions/` no commit.
- [ ] Execute `pytest` para garantir que todos os testes continuam passando.

### Evitando cliques múltiplos em botões

Use a função `executarAcaoComFeedback` definida em `src/static/js/app.js` para
desabilitar botões enquanto uma ação assíncrona é executada, evitando que o
usuário clique várias vezes.

```html
<button id="btnSalvar" class="btn btn-primary">
  <span class="spinner-border spinner-border-sm d-none" role="status"></span>
  <span class="btn-text">Salvar</span>
</button>

<input id="btnExcluir" type="submit" class="btn btn-danger"
       value="Excluir">
```

```javascript
// Exemplo genérico de uso com <button>
document.getElementById('btnSalvar').addEventListener('click', () => {
  executarAcaoComFeedback(document.getElementById('btnSalvar'), async () => {
    await chamarAPI('/exemplo', 'POST');
  });
});

// Exemplo usando <input type="submit">
document.getElementById('btnExcluir').addEventListener('click', (e) => {
  e.preventDefault();
  executarAcaoComFeedback(e.currentTarget, async () => {
    await chamarAPI('/exemplo', 'DELETE');
  });
});
```

