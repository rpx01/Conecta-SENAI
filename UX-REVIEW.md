# UX Review – Conecta-SENAI

## Resumo das Mudanças
- Implementação de um design system centralizado (`tokens.css`) para tipografia fluida, espaçamentos em escala de 4px e paleta institucional do SENAI.
- Reescrita completa do `styles.css` com reset consistente, componentes padronizados (botões de 44px, cards com sombras suaves, formulários e tabelas responsivas) e utilitários de acessibilidade.
- Atualização de todos os demais estilos (brand, filtros, notícias, login, menu suspenso, treinamentos) para consumir os tokens e eliminar valores mágicos.
- Ajustes na página de seleção de sistemas para alinhar containers, badges e rodapé ao novo visual soft & clean.

## Páginas Impactadas
- Seleção de Sistemas (`src/static/selecao-sistema.html`).
- Portal de Notícias (`src/static/css/noticias.css`).
- Telas de login e branding compartilhado (`src/static/css/login.css`, `src/static/css/brand.css`).
- Componentes de filtros e menus (`src/static/css/filtros-tabela.css`, `src/static/css/tabela-filtro.css`, `src/static/css/components/filter.css`, `src/static/css/menu-suspenso.css`).
- Módulo de treinamentos (ocultação de colunas) e estilos globais (`src/static/css/treinamentos.css`, `src/static/css/styles.css`).

## Checklist de Validação
- [x] Nenhum texto extrapola seu contêiner na largura de tela de **320px**.
- [x] A fonte base do `body` respeita `var(--font-size-md)` e os cabeçalhos (`h1`, `h2`, etc.) usam os tokens de `clamp()`.
- [x] Os botões padrão têm **44px** de altura, e os botões pequenos, **36px**.
- [x] Tabelas e cards não causam overflow horizontal, utilizando `break-word` ou `truncate` quando necessário.
- [x] O contraste de cores entre texto e fundo atende ao critério AA da WCAG.
- [x] O estado `:focus-visible` é claro e funcional.
- [x] **Nenhum `!important`** foi usado para sobrescrever estilos.
- [x] A navegação principal e sidebars colapsam de forma limpa em telas menores que 768px.

## Próximos Passos
- Realizar uma rodada de testes exploratórios com usuários para validar a nova hierarquia visual e oportunidades de microinterações.
- Revisitar ícones e ilustrações para garantir consistência com o novo visual soft & clean.
