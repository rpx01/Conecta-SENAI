(function(){
  function inicializarFiltrosTabela(selector){
    const table = document.querySelector(selector);
    if(!table) return;
    const tbody = table.tBodies[0];
    if(!tbody) return;

    // limpar instâncias anteriores
    table.querySelectorAll('.filter-toggle').forEach(el=>el.remove());
    table.querySelectorAll('.filter-menu').forEach(el=>el.remove());

    const rows = Array.from(tbody.rows);
    const filtros = {};

    const fecharMenus = () => {
      table.querySelectorAll('.filter-menu').forEach(m=>m.classList.add('hidden'));
    };
    document.addEventListener('click', fecharMenus);

    Array.from(table.tHead.rows[0].cells).forEach((th, index) => {
      if(th.dataset.noFilter === 'true' || th.dataset.filterable !== 'true') return;

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'filter-toggle';
      btn.textContent = '▼';
      th.appendChild(btn);

      const menu = document.createElement('div');
      menu.className = 'filter-menu hidden';
      menu.innerHTML = `
        <input type="text" class="search" placeholder="Buscar...">
        <div class="options"></div>
        <div class="actions">
          <button type="button" class="btn aplicar">Aplicar</button>
          <button type="button" class="btn limpar">Limpar</button>
          <button type="button" class="btn asc">A→Z</button>
          <button type="button" class="btn desc">Z→A</button>
        </div>`;
      th.appendChild(menu);

      const searchInput = menu.querySelector('.search');
      const optionsDiv = menu.querySelector('.options');
      const applyBtn = menu.querySelector('.aplicar');
      const clearBtn = menu.querySelector('.limpar');
      const ascBtn = menu.querySelector('.asc');
      const descBtn = menu.querySelector('.desc');

      const valores = [...new Set(rows.map(r => (r.cells[index]?.innerText || '').trim()))]
        .sort((a,b)=>a.localeCompare(b,'pt-BR'));
      valores.forEach(v=>{
        const label = document.createElement('label');
        const cb = document.createElement('input');
        cb.type='checkbox';
        cb.value=v;
        cb.checked=true;
        label.appendChild(cb);
        label.appendChild(document.createTextNode(' '+v));
        optionsDiv.appendChild(label);
      });

      searchInput.addEventListener('input', ()=>{
        const termo = searchInput.value.toLowerCase();
        Array.from(optionsDiv.children).forEach(label=>{
          label.style.display = label.textContent.toLowerCase().includes(termo)?'':'none';
        });
      });

      btn.addEventListener('click', (e)=>{
        e.stopPropagation();
        const oculto = menu.classList.contains('hidden');
        fecharMenus();
        if(oculto) menu.classList.remove('hidden');
      });
      menu.addEventListener('click', e=>e.stopPropagation());

      const aplicar = ()=>{
        const selecionados = Array.from(optionsDiv.querySelectorAll('input:checked')).map(cb=>cb.value);
        const termo = searchInput.value.trim().toLowerCase();
        if(selecionados.length === valores.length && !termo){
          delete filtros[index];
        } else {
          filtros[index] = {valores: selecionados, termo};
        }
        aplicarFiltros();
        menu.classList.add('hidden');
      };

      applyBtn.addEventListener('click', aplicar);
      clearBtn.addEventListener('click', ()=>{
        searchInput.value='';
        optionsDiv.querySelectorAll('input').forEach(cb=>cb.checked=true);
        delete filtros[index];
        aplicarFiltros();
        menu.classList.add('hidden');
      });
      ascBtn.addEventListener('click', ()=>{ordenar(index,'asc'); menu.classList.add('hidden');});
      descBtn.addEventListener('click', ()=>{ordenar(index,'desc'); menu.classList.add('hidden');});
    });

    function aplicarFiltros(){
      rows.forEach(r=>r.style.display='');
      rows.forEach(r=>{
        for(const [idx,f] of Object.entries(filtros)){
          const texto = (r.cells[idx]?.innerText || '').trim();
          const textoLower = texto.toLowerCase();
          if(f.termo && !textoLower.includes(f.termo)) { r.style.display='none'; break; }
          if(f.valores && f.valores.length && !f.valores.includes(texto)) { r.style.display='none'; break; }
        }
      });
    }

    function ordenar(colIdx, dir){
      const visiveis = rows.filter(r=>r.style.display!=='none');
      const ocultos = rows.filter(r=>r.style.display==='none');
      const collator = new Intl.Collator('pt-BR',{numeric:true,sensitivity:'base'});
      visiveis.sort((a,b)=>{
        const aT = (a.cells[colIdx]?.innerText || '').trim();
        const bT = (b.cells[colIdx]?.innerText || '').trim();
        return dir==='asc'?collator.compare(aT,bT):collator.compare(bT,aT);
      });
      tbody.append(...visiveis, ...ocultos);
    }

    const resetBtn = document.querySelector('[data-reset-filtros]');
    if(resetBtn){
      resetBtn.addEventListener('click', ()=>{
        Object.keys(filtros).forEach(k=>delete filtros[k]);
        table.querySelectorAll('.filter-menu .search').forEach(i=>i.value='');
        table.querySelectorAll('.filter-menu .options input').forEach(cb=>cb.checked=true);
        aplicarFiltros();
      });
    }
  }
  window.inicializarFiltrosTabela = inicializarFiltrosTabela;
})();
