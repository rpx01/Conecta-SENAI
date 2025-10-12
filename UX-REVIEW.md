# UX Review Log

## 2024-05-06 — Soft & Clean Refresh

### Mudanças-chave
- Introduzido `src/static/css/tokens.css` com tipografia fluida (`clamp`), escala de espaçamentos e tokens de cor, aplicando-os via `@import` em toda a base de estilos.
- Harmonização dos componentes Bootstrap customizados em `styles.css` para botões (44px/36px), cards com sombras suaves, tabelas responsivas com `wrap/ellipsis` e formulários com controles de 40px.
- Ajuste dos temas específicos (`brand.css`, `login.css`, menus e filtros) para usar tokens e reduzir fontes grandes, removendo `font-size` inline nas páginas de dashboards/laboratórios.

### Páginas e áreas revisadas
- Estilos globais: `src/static/css/styles.css`, `brand.css`.
- Páginas estáticas com ajustes diretos: `laboratorios/calendario.html`, `ocupacao/dashboard.html`.
- Telas de login (`login.css`) e componentes de filtro (`filtros-tabela.css`, `tabela-filtro.css`, `components/filter.css`) e menu lateral (`menu-suspenso.css`).

### Checklist de testes
- [x] Nenhum texto extrapola contêiner em 320px (verificado via revisão responsiva manual usando tokens de `min-width: 0`).
- [x] Tipografia base ≤ `var(--font-size-md)` com headings escalonados (`clamp`) nos tokens.
- [x] Botões padrão entre 36–44px e fonte ≤ `var(--font-size-sm)`.
- [x] Tabelas/cards configurados com `wrap`/`truncate` e scroll suave.
- [x] Contraste AA mantido com azul institucional e foco visível (`:focus-visible`).
- [x] Remoção de `!important` desnecessários (mantidos apenas onde Bootstrap exige) e uso consistente de tokens.
- [x] Navegação/sidebars com largura fluida e colapso <768px.

### Pendências
- Validar visual final em dispositivos reais (iOS/Android) para garantir suavidade das transições e espaçamentos na prática.
