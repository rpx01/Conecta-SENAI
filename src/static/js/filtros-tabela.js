// src/static/js/filtros-tabela.js
// Lógica de filtros e ordenação para a tabela de Planejamento Trimestral
// Mantém o estado dos filtros por coluna e aplica sobre as linhas da tabela.

(function(){
  let tabela = null;
  const filtros = {}; // {col: [valores]}
  const colIndex = {}; // {col: index}

  function inicializarFiltrosTabela(selector){
    tabela = document.querySelector(selector);
    if(!tabela) return;

    const thead = tabela.tHead;
    if(!thead) return;

    const headers = Array.from(thead.rows[0].cells);
    headers.forEach((th, idx) => {
      const btn = th.querySelector('.filter-btn');
      if(!btn) return;
      const col = btn.getAttribute('data-filter-for');
      colIndex[col] = idx;

      const dd = th.querySelector('.filter-dropdown');
      if(!dd) return;
      dd.innerHTML = `
        <div class="filter-card">
          <div class="filter-head">
            <input type="text" class="form-control form-control-sm filter-search" placeholder="Buscar...">
          </div>
          <div class="filter-list" role="group" aria-label="Opções de filtro"></div>
          <div class="filter-actions">
            <div class="sort-group" role="group" aria-label="Ordenação">
              <button type="button" class="btn btn-light btn-sm sort-asc" title="Ordenar A–Z">A–Z</button>
              <button type="button" class="btn btn-light btn-sm sort-desc" title="Ordenar Z–A">Z–A</button>
            </div>
            <div class="cta-group">
              <button type="button" class="btn btn-primary btn-sm apply">Aplicar</button>
              <button type="button" class="btn btn-outline-secondary btn-sm clear">Limpar</button>
            </div>
          </div>
          <div class="filter-foot text-muted">Pressione Esc para fechar</div>
        </div>`;
      const list = dd.querySelector('.filter-list');
      const valores = [...new Set(Array.from(tabela.tBodies[0].rows).map(r => (r.cells[idx]?.innerText || '').trim()))]
        .sort((a,b)=>a.localeCompare(b,'pt-BR'));

      valores.forEach(v => {
        const safe = typeof escapeHTML === 'function' ? escapeHTML(v) : v;
        list.insertAdjacentHTML('beforeend',
          `<label class="filter-item"><input type="checkbox" value="${safe}" checked><span>${safe || '&lt;vazio&gt;'}</span></label>`);
      });

      window.filterAttachHandlers && window.filterAttachHandlers(dd);
    });

    const resetBtn = document.querySelector('[data-reset-filtros]');
    if(resetBtn){
      resetBtn.addEventListener('click', () => {
        Object.keys(filtros).forEach(k => delete filtros[k]);
        document.querySelectorAll('.filter-dropdown input[type="checkbox"]').forEach(i=>i.checked = false);
        aplicarFiltros();
      });
    }
  }

  function aplicarFiltro(col, valores){
    if(!tabela || !(col in colIndex)) return;
    const idx = colIndex[col];
    filtros[col] = valores && valores.length ? valores : null;
    aplicarFiltros();
  }

  function limparFiltro(col){
    if(col in filtros) delete filtros[col];
    aplicarFiltros();
  }

  function aplicarFiltros(){
    if(!tabela) return;
    const rows = Array.from(tabela.tBodies[0].rows);
    rows.forEach(r => {
      let visivel = true;
      for(const [col, valores] of Object.entries(filtros)){
        if(!valores || !valores.length) continue;
        const idx = colIndex[col];
        const texto = (r.cells[idx]?.innerText || '').trim();
        if(!valores.includes(texto)) { visivel = false; break; }
      }
      r.style.display = visivel ? '' : 'none';
    });
  }

  function ordenarColuna(col, dir){
    if(!tabela || !(col in colIndex)) return;
    const idx = colIndex[col];
    const tbody = tabela.tBodies[0];
    const rows = Array.from(tbody.rows);
    const collator = new Intl.Collator('pt-BR',{numeric:true,sensitivity:'base'});
    rows.sort((a,b)=>{
      const aT = (a.cells[idx]?.innerText || '').trim();
      const bT = (b.cells[idx]?.innerText || '').trim();
      return dir==='desc' ? collator.compare(bT,aT) : collator.compare(aT,bT);
    });
    tbody.append(...rows);
  }

  window.inicializarFiltrosTabela = inicializarFiltrosTabela;
  window.aplicarFiltro = aplicarFiltro;
  window.limparFiltro = limparFiltro;
  window.ordenarColuna = ordenarColuna;
})();
