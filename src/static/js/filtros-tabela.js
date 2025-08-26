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
      const col = btn.getAttribute('data-col');
      colIndex[col] = idx;

      const menu = th.querySelector('.filter-menu [data-role="filter-options"]');
      if(!menu) return;

      const valores = [...new Set(Array.from(tabela.tBodies[0].rows).map(r => (r.cells[idx]?.innerText || '').trim()))]
        .sort((a,b)=>a.localeCompare(b,'pt-BR'));

      valores.forEach(v => {
        const id = `${col}-${btoa(unescape(encodeURIComponent(v))).replace(/=/g,'')}`;
        menu.insertAdjacentHTML('beforeend',
          `<div class="form-check"><input class="form-check-input" type="checkbox" id="${id}" value="${v}" checked>
          <label class="form-check-label" for="${id}">${v || '&lt;vazio&gt;'}</label></div>`);
      });
    });

    const resetBtn = document.querySelector('[data-reset-filtros]');
    if(resetBtn){
      resetBtn.addEventListener('click', () => {
        Object.keys(filtros).forEach(k => delete filtros[k]);
        tabela.querySelectorAll('[data-role="filter-options"] input[type="checkbox"]').forEach(i=>i.checked = true);
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
