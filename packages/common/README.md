# conectasenai-common

Utilitários compartilhados entre os aplicativos do monorepositório.

## Conteúdo

- **`email`**: helpers para normalizar endereços e montar contextos utilizados nas
  rotinas de disparo de e-mails.
- **`validators`**: expressões e funções de validação reutilizáveis.

## Desenvolvimento local

Instale o pacote em modo editável a partir da raiz do repositório:

```bash
poetry install --with dev
```

ou diretamente pela pasta do pacote:

```bash
cd packages/common
poetry install
```
