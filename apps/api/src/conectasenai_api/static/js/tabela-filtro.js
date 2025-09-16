/* Filtros e ordenação “estilo Excel” para a tabela de Planejamento Trimestral
   - JS puro, sem libs externas
   - Coloquei utilitários de parsing para data BR, horário e número
   - Suporta múltiplos filtros por coluna e ordenação estável
*/

(() => {
  const STORAGE_KEY = 'planejamento-trimestral-filtros';

  const toBRDate = (s) => {
    // "dd/mm/yyyy" -> timestamp
    const [d, m, y] = s.trim().split('/').map(Number);
    if (!d || !m || !y) return Number.MAX_SAFE_INTEGER;
    return new Date(y, m - 1, d).getTime();
  };

  const toMinutes = (s) => {
    // "08:00 às 10:00" -> minutos do início
    if (!s) return Number.MAX_SAFE_INTEGER;
    const inicio = (s.split('às')[0] || s).trim();
    const [h, m] = inicio.split(':').map(Number);
    if (isNaN(h) || isNaN(m)) return Number.MAX_SAFE_INTEGER;
    return h * 60 + m;
  };

  const toNumber = (s) => {
    const n = Number(String(s).replace(/\D+/g, ''));
    return isNaN(n) ? Number.MAX_SAFE_INTEGER : n;
  };

  // Comparadores por tipo
  const comparators = {
    text: (a, b) => a.localeCompare(b, 'pt-BR', { sensitivity: 'base' }),
    date: (a, b) => toBRDate(a) - toBRDate(b),
    time: (a, b) => toMinutes(a) - toMinutes(b),
    number: (a, b) => toNumber(a) - toNumber(b),
  };

  const getComparator = (type) => comparators[type] || comparators.text;

  // Lê/Salva estado
  const loadState = () => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
    catch { return {}; }
  };
  const saveState = (state) => localStorage.setItem(STORAGE_KEY, JSON.stringify(state));

  // Coleta valores únicos da coluna
  const uniqueValues = (rows, colIdx) => {
    const set = new Set();
    rows.forEach(tr => set.add(tr.cells[colIdx]?.innerText.trim() ?? ''));
    return Array.from(set).sort((a, b) => a.localeCompare(b, 'pt-BR', { sensitivity: 'base' }));
  };

  // Aplica filtros em todas as colunas
  const applyFilters = (table, state) => {
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);

    rows.forEach(tr => tr.style.display = '');

    Object.entries(state.filters || {}).forEach(([idx, f]) => {
      const colIdx = Number(idx);
      if (!f) return;

      const textQuery = (f.text || '').trim().toLowerCase();
      const allowed = f.allowed || null;

      rows.forEach(tr => {
        const cellVal = tr.cells[colIdx]?.innerText ?? '';
        const v = cellVal.trim();
        let ok = true;

        if (textQuery) ok = v.toLowerCase().includes(textQuery);
        if (ok && allowed && allowed.length) ok = allowed.includes(v);

        if (!ok) tr.style.display = 'none';
      });
    });
  };

  // Ordena linhas visíveis
  const sortBy = (table, colIdx, dir, type) => {
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);
    const cmp = getComparator(type);

    const visible = rows.filter(r => r.style.display !== 'none');
    const hidden  = rows.filter(r => r.style.display === 'none');

    visible.sort((ra, rb) => {
      const a = ra.cells[colIdx]?.innerText.trim() ?? '';
      const b = rb.cells[colIdx]?.innerText.trim() ?? '';
      const base = cmp(a, b);
      return dir === 'desc' ? -base : base;
    });

    // Stable: mantém ordem relativa dos escondidos
    tbody.append(...visible, ...hidden);
  };

  // Cria menu de filtro/ordenação para um <th>
  const buildMenuForHeader = (table, th, colIdx, state) => {
    if (th.dataset.filter === 'off') return; // pular “Ações”
    th.classList.add('th-filter');

    const label = th.textContent.trim();
    const type = th.dataset.type || inferTypeFromHeader(label);

    const btn = document.createElement('button');
    btn.className = 'filter-btn';
    btn.type = 'button';
    btn.setAttribute('aria-label', `Filtro e ordenação da coluna ${label}`);
    btn.innerHTML = '🔽';

    const menu = document.createElement('div');
    menu.className = 'filter-menu';
    menu.innerHTML = `
      <div class="filter-section">
        <h6>Ordenar</h6>
        <div class="d-grid gap-1">
          <button type="button" class="btn btn-sm btn-light" data-action="sort" data-dir="asc">A → Z</button>
          <button type="button" class="btn btn-sm btn-light" data-action="sort" data-dir="desc">Z → A</button>
        </div>
      </div>
      <div class="filter-section">
        <h6>Filtrar por texto</h6>
        <input type="text" class="form-control form-control-sm" data-role="text-filter" placeholder="Digite para filtrar...">
      </div>
      <div class="filter-section">
        <h6>Selecionar valores</h6>
        <div class="mb-2 d-flex gap-2">
          <button type="button" class="btn btn-sm btn-outline-secondary" data-role="select-all">Selecionar tudo</button>
          <button type="button" class="btn btn-sm btn-outline-secondary" data-role="clear-all">Limpar</button>
        </div>
        <div class="values" data-role="values"></div>
      </div>
      <div class="menu-actions">
        <button type="button" class="btn btn-sm btn-secondary" data-role="clear">Limpar filtro</button>
        <button type="button" class="btn btn-sm btn-primary" data-role="apply">Aplicar</button>
      </div>
    `;

    // Backdrop para fechar ao clicar fora
    const backdrop = document.createElement('div');
    backdrop.className = 'filter-backdrop';

    const current = (state.filters?.[colIdx]) || { text: '', allowed: [] };

    const rows = Array.from(table.tBodies[0].rows);
    const container = menu.querySelector('[data-role="values"]');
    const values = uniqueValues(rows, colIdx);

    // Render checkboxes
    values.forEach(v => {
      const id = `v-${colIdx}-${btoa(encodeURIComponent(v)).replace(/=/g,'')}`;
      const wrap = document.createElement('div');
      wrap.className = 'form-check';
      wrap.innerHTML = `
        <input class="form-check-input" type="checkbox" id="${id}" value="${v}">
        <label class="form-check-label" for="${id}">${v || '<vazio>'}</label>
      `;
      container.appendChild(wrap);
    });

    const checkInputs = () => Array.from(container.querySelectorAll('input[type="checkbox"]'));

    // Estado inicial (se existir)
    if (current.allowed?.length) {
      checkInputs().forEach(i => i.checked = current.allowed.includes(i.value));
    } else {
      checkInputs().forEach(i => i.checked = true);
    }
    menu.querySelector('[data-role="text-filter"]').value = current.text || '';

    // Ações do menu
    menu.addEventListener('click', (e) => {
      const t = e.target;
      if (!(t instanceof HTMLElement)) return;

      if (t.dataset.action === 'sort') {
        const dir = t.dataset.dir;
        sortBy(table, colIdx, dir, type);
        closeMenu();
      }

      if (t.dataset.role === 'select-all') {
        checkInputs().forEach(i => i.checked = true);
      }

      if (t.dataset.role === 'clear-all') {
        checkInputs().forEach(i => i.checked = false);
      }

      if (t.dataset.role === 'clear') {
        // limpar filtro desta coluna
        state.filters = state.filters || {};
        delete state.filters[colIdx];
        saveState(state);
        applyFilters(table, state);
        closeMenu();
      }

      if (t.dataset.role === 'apply') {
        const text = menu.querySelector('[data-role="text-filter"]').value || '';
        const allowed = checkInputs().filter(i => i.checked).map(i => i.value);

        // Se todos marcados e sem texto, não salvar filtro
        const everyChecked = allowed.length === checkInputs().length;
        state.filters = state.filters || {};
        if (!text.trim() && everyChecked) {
          delete state.filters[colIdx];
        } else {
          state.filters[colIdx] = { text, allowed };
        }
        saveState(state);
        applyFilters(table, state);
        closeMenu();
      }
    });

    const openMenu = () => {
      document.body.appendChild(backdrop);
      backdrop.classList.add('show');
      menu.classList.add('show');
    };

    const closeMenu = () => {
      menu.classList.remove('show');
      backdrop.classList.remove('show');
      backdrop.remove();
    };

    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (menu.classList.contains('show')) closeMenu(); else openMenu();
    });

    backdrop.addEventListener('click', closeMenu);

    th.appendChild(btn);
    th.appendChild(menu);
  };

  // Inferência simples de tipo pelo título
  const inferTypeFromHeader = (label) => {
    const t = label.toLowerCase();
    if (t.includes('data')) return 'date';
    if (t.includes('horário') || t.includes('horario')) return 'time';
    if (t === 'c.h.' || t.includes('carga')) return 'number';
    return 'text';
  };

  // Reset global
  const installGlobalReset = (table, state) => {
    const btn = document.querySelector('[data-reset-filtros]');
    if (!btn) return;
    btn.addEventListener('click', () => {
      state.filters = {};
      saveState(state);
      applyFilters(table, state);
    });
  };

  // Bootstrap
  document.addEventListener('DOMContentLoaded', () => {
    const table = document.querySelector('#tabela-planejamento') ||
                  document.querySelector('table[data-table="planejamento-trimestral"]');
    if (!table) return;

    // Garantir data-type nos THs (pode ser ajustado no HTML também)
    const headers = Array.from(table.tHead.rows[0].cells);
    headers.forEach((th, idx) => {
      const label = th.textContent.trim().toLowerCase();
      if (label === 'ações' || th.dataset.filter === 'off') th.dataset.filter = 'off';
      if (!th.dataset.type) th.dataset.type = inferTypeFromHeader(label);
    });

    const state = loadState();

    headers.forEach((th, idx) => buildMenuForHeader(table, th, idx, state));

    // Aplica filtros persistidos ao carregar
    applyFilters(table, state);
    installGlobalReset(table, state);
  });
})();
