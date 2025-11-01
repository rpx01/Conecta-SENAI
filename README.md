# Conecta SENAI

Conecta SENAI é uma plataforma web construída com Flask que centraliza o gerenciamento de recursos acadêmicos do SENAI. O sistema integra reservas de laboratórios e salas, treinamentos corporativos, suporte de TI e divulgação de notícias em um único portal, oferecendo aos gestores visibilidade operacional e aos colaboradores uma experiência consistente para realizar solicitações e consultar informações atualizadas.

## Como executar o projeto localmente

1. **Clonar o repositório**
   ```bash
   git clone https://github.com/<OWNER>/<REPO>.git
   cd Conecta-SENAI
   ```

2. **Criar e ativar um ambiente virtual**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # .venv\Scripts\activate   # Windows PowerShell
   ```

3. **Instalar as dependências Python**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configurar variáveis de ambiente**
   ```bash
   cp .env.example .env
   # edite o arquivo .env com as credenciais do banco, Redis, provedores de e-mail etc.
   ```

5. **Aplicar as migrações do banco de dados**
   ```bash
   flask --app src.main db upgrade
   ```

6. **Iniciar o servidor de desenvolvimento**
   ```bash
   flask --app src.main run
   ```

Após esses passos, a aplicação estará disponível em `http://127.0.0.1:5000`. Os módulos internos expõem APIs REST autenticadas por JWT e telas HTML renderizadas com Jinja2 para a interface administrativa.

## Estrutura do Projeto

A seguir, um panorama dos diretórios principais em `src/`:

- `src/blueprints/` – Blueprints voltados para fluxos de autenticação e páginas especializadas.
- `src/routes/` – Views e endpoints REST organizados por domínio (notícias, treinamentos, suporte de TI etc.).
- `src/models/` – Modelos ORM do SQLAlchemy que representam as tabelas do banco.
- `src/services/` – Camada de serviços que concentra regras de negócio e integrações externas.
- `src/repositories/` – Acesso a dados e funções utilitárias para consultas complexas.
- `src/templates/` – Templates Jinja2 responsáveis pelas páginas HTML apresentadas pela aplicação.
- `src/static/` – Arquivos estáticos consumidos pelos templates (CSS, JavaScript, imagens e uploads).
- `migrations/` – Scripts do Alembic usados para versionar o esquema do banco de dados.

Outros diretórios importantes:

- `tests/` – Casos de teste automatizados.
- `docs/` – Documentação complementar, incluindo design system e guias de contribuição.
- `scripts/` – Utilitários para tarefas recorrentes, como geração de migrações automáticas.

## Observabilidade e Boas Práticas

- Os logs seguem formato estruturado em JSON; utilize ferramentas como `jq` para filtragem.
- O monitoramento de erros integra-se ao Sentry. Um endpoint `/debug-sentry` está disponível para validar a configuração.
- Secrets e credenciais devem ser definidos apenas por variáveis de ambiente. Consulte `.env.example` para a lista completa de parâmetros esperados.

## Contribuição

1. Crie um branch a partir de `main` com uma descrição clara do que será implementado.
2. Garanta que os testes automatizados (`pytest`) e checagens estáticas sejam executados com sucesso.
3. Abra um Pull Request descrevendo o contexto da alteração, passos de validação e screenshots quando aplicável.

Para detalhes sobre versões e mudanças históricas consulte [CHANGELOG.md](CHANGELOG.md). O projeto possui pipelines de integração contínua que executam lint, testes e verificação de segurança a cada nova contribuição.
