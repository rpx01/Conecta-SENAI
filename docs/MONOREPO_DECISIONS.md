# Decisões de Arquitetura do Monorepo

Este documento resume as diretrizes para organização do monorepositório do
Conecta-SENAI.

## Fronteiras principais

- **Apps (`apps/`)**: contêm código executável. Cada app mantém seu próprio
  `pyproject.toml`, dependências e pipelines específicos.
  - `apps/api`: serviço Flask responsável pelas APIs e pela renderização das
    telas HTML servidas pelo backend.
- **Packages (`packages/`)**: bibliotecas reutilizáveis publicadas como
  dependências locais. O diretório segue o layout ``<nome>/conectasenai_<domínio>``.
  - `packages/common`: utilidades compartilhadas (validações, helpers de e-mail,
    etc.).
- **Infraestrutura (`infra/`)**: compose, arquivos de ambiente e automações de
  deploy.

## Convenções de nome

- Pacotes Python expostos publicamente utilizam o prefixo `conectasenai_`.
- Módulos internos dos apps devem ser importados usando o namespace do pacote
  (`conectasenai_api.*`). Importações absolutas antigas (`src.*`) não são mais
  suportadas.
- Funções utilitárias genéricas devem residir em `packages/common`. Evite criar
  novas cópias dentro dos apps.

## Adicionando novos módulos

1. **Biblioteca reutilizável**: crie um novo diretório em `packages/` com seu
   próprio `pyproject.toml`. Siga o modelo de `packages/common`.
2. **Novo app**: adicione uma pasta em `apps/` contendo `src/`, `pyproject.toml`
   e Dockerfile dedicados. Atualize os workflows para incluir a nova pasta.
3. **Ferramentas de CI**: utilize o workflow `.github/workflows/ci.yml` como
   referência para adicionar novos filtros de caminho.

## Dependências locais

- Os apps devem referenciar bibliotecas internas usando dependências do tipo
  `path` no `pyproject.toml`.
- Ao rodar `poetry install` na raiz, tanto o app quanto os packages são
  instalados em modo editável, facilitando o desenvolvimento integrado.

## Estrutura de diretórios

```
/
├─ apps/
│  └─ <app>/
│     ├─ src/<pacote_app>/
│     ├─ migrations/
│     ├─ Dockerfile
│     └─ pyproject.toml
├─ packages/
│  └─ <package>/
│     ├─ conectasenai_<domínio>/
│     └─ pyproject.toml
└─ infra/
    └─ docker-compose.yml
```

## Boas práticas

- Sempre execute `poetry install --with dev` a partir do diretório do app antes
  de rodar testes ou migrações.
- Utilize o compose (`infra/docker-compose.yml`) para validar o container final.
- Commit apenas código dentro das pastas correspondentes para facilitar o filtro
  de mudanças nos pipelines.
