(() => {
  const table = document.getElementById('tabela-planejamento');
  if (!table) return;

  const pop = document.getElementById('filter-popover');
  const searchInput = pop.querySelector('.filter-search');
  const optionsBox = pop.querySelector('.filter-options');
  const checkAll = pop.querySelector('.check-all');
  const btnAZ = pop.querySelector('.btn-az');
  const btnZA = pop.querySelector('.btn-za');
  const btnApply = pop.querySelector('.btn-apply');
  const btnClear = pop.querySelector('.btn-clear');

  const activeFilters = new Map(); // colIndex -> Set(values)
  let currentCol = null;
  let anchorBtn = null;

  let rows = Array.from(table.tBodies[0].rows);

  function getCellText(row, colIndex) {
    const cell = row.cells[colIndex];
    return (cell ? cell.innerText : '').trim();
  }

  function uniqueValues(colIndex) {
    const set = new Set();
    rows.forEach(r => {
      if (r.style.display === 'none') { /* still collect all values */ }
      set.add(getCellText(r, colIndex));
    });
    return Array.from(set).filter(v => v !== '');
  }

  function buildOptions(values, preselected) {
    optionsBox.innerHTML = '';
    const selected = preselected || new Set(values);

    values.forEach(v => {
      const id = 'opt-' + currentCol + '-' + btoa(unescape(encodeURIComponent(v))).replace(/=/g,'');
      const wrap = document.createElement('label');
      wrap.setAttribute('for', id);

      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.id = id;
      cb.checked = selected.has(v);
      cb.dataset.value = v;

      const txt = document.createElement('span');
      txt.textContent = v;

      wrap.appendChild(cb);
      wrap.appendChild(txt);
      optionsBox.appendChild(wrap);
    });

    checkAll.checked = selected.size === values.length;
  }

  function openPopover(btn, colIndex) {
    rows = Array.from(table.tBodies[0].rows);
    anchorBtn = btn;
    currentCol = Number(colIndex);

    // Estado prévio
    const allVals = uniqueValues(currentCol);
    const selected = activeFilters.get(currentCol) || new Set(allVals);

    buildOptions(allVals, selected);
    searchInput.value = '';

    // Posiciona ao lado do botão
    const r = btn.getBoundingClientRect();
    const top = window.scrollY + r.bottom + 6;
    const left = Math.min(window.scrollX + r.left, window.scrollX + window.innerWidth - 280);

    pop.style.top = `${top}px`;
    pop.style.left = `${left}px`;

    // UI
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('is-active'));
    btn.classList.add('is-active');
    pop.classList.remove('hidden');
    searchInput.focus();
  }

  function closePopover() {
    pop.classList.add('hidden');
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('is-active'));
    anchorBtn = null;
    currentCol = null;
  }

  function applyFilters() {
    // Lê checks atuais do popover
    if (currentCol != null) {
      const chosen = new Set(
        Array.from(optionsBox.querySelectorAll('input[type="checkbox"]'))
          .filter(cb => cb.checked)
          .map(cb => cb.dataset.value)
      );
      activeFilters.set(currentCol, chosen);
    }

    // Remove filtros vazios
    for (const [col, set] of activeFilters) {
      if (!set || set.size === 0) activeFilters.delete(col);
    }

    // Aplica
    rows.forEach(row => {
      const visible = Array.from(activeFilters.entries()).every(([col, allowed]) => {
        const val = getCellText(row, col);
        return allowed.has(val);
      });
      row.style.display = visible ? '' : 'none';
    });

    closePopover();
  }

  function clearFiltersForCurrent() {
    if (currentCol != null) {
      activeFilters.delete(currentCol);
      applyFilters();
    }
  }

  function sortBy(colIndex, asc = true) {
    const collator = new Intl.Collator('pt-BR', { numeric: true, sensitivity: 'base' });
    rows.sort((a, b) => {
      const A = getCellText(a, colIndex);
      const B = getCellText(b, colIndex);
      return asc ? collator.compare(A, B) : collator.compare(B, A);
    });
    const tbody = table.tBodies[0];
    rows.forEach(r => tbody.appendChild(r));
  }

  // Eventos globais
  table.addEventListener('click', (e) => {
    const btn = e.target.closest('.filter-btn');
    if (!btn) return;
    e.stopPropagation();
    openPopover(btn, btn.dataset.col);
  });

  document.addEventListener('click', (e) => {
    if (!pop.classList.contains('hidden') && !pop.contains(e.target) && !e.target.closest('.filter-btn')) {
      closePopover();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !pop.classList.contains('hidden')) {
      closePopover();
    }
  });

  // Buscar dentro do popover
  searchInput.addEventListener('input', () => {
    const q = searchInput.value.toLowerCase();
    optionsBox.querySelectorAll('label').forEach(lab => {
      const text = lab.querySelector('span').textContent.toLowerCase();
      lab.style.display = text.includes(q) ? '' : 'none';
    });
  });

  // Selecionar tudo
  checkAll.addEventListener('change', () => {
    const on = checkAll.checked;
    optionsBox.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = on);
  });

  // Ações
  btnApply.addEventListener('click', applyFilters);
  btnClear.addEventListener('click', clearFiltersForCurrent);
  btnAZ.addEventListener('click', () => currentCol != null && sortBy(currentCol, true));
  btnZA.addEventListener('click', () => currentCol != null && sortBy(currentCol, false));

  // Reposicionar em scroll/resize
  window.addEventListener('scroll', () => {
    if (anchorBtn && !pop.classList.contains('hidden')) openPopover(anchorBtn, currentCol);
  }, { passive: true });
  window.addEventListener('resize', () => {
    if (anchorBtn && !pop.classList.contains('hidden')) openPopover(anchorBtn, currentCol);
  });
})();
