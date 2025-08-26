(function(){
  const btn = document.getElementById('btnFiltros');
  const menu = document.getElementById('menuFiltros');

  if(!btn || !menu) return;

  const place = () => {
    const bcr = btn.getBoundingClientRect();
    const scrollX = window.scrollX || document.documentElement.scrollLeft;
    const scrollY = window.scrollY || document.documentElement.scrollTop;

    // posição preferida: abaixo e alinhado à esquerda
    let top = bcr.bottom + scrollY + 8;  // 8px gap
    let left = bcr.left + scrollX;

    // manter dentro da janela
    const menuWidth = menu.offsetWidth || 280;
    const menuHeight = menu.offsetHeight || 200;
    const vw = document.documentElement.clientWidth;
    const vh = document.documentElement.clientHeight;

    if (left + menuWidth > scrollX + vw - 8) {
      left = Math.max(scrollX + 8, (bcr.right + scrollX) - menuWidth);
    }
    if (top + menuHeight > scrollY + vh - 8) {
      // se faltar espaço abaixo, abre acima
      const above = (bcr.top + scrollY) - menuHeight - 8;
      if (above > scrollY + 8) top = above;
    }

    menu.style.left = `${left}px`;
    menu.style.top  = `${top}px`;
  };

  const open = () => {
    menu.hidden = false;
    btn.setAttribute('aria-expanded', 'true');
    place();
    document.addEventListener('click', onDocClick, { capture: true });
    window.addEventListener('resize', place);
    window.addEventListener('scroll', place, { passive: true });
  };

  const close = () => {
    menu.hidden = true;
    btn.setAttribute('aria-expanded', 'false');
    document.removeEventListener('click', onDocClick, { capture: true });
    window.removeEventListener('resize', place);
    window.removeEventListener('scroll', place, { passive: true });
  };

  const onDocClick = (e) => {
    if (menu.contains(e.target) || btn.contains(e.target)) return;
    close();
  };

  btn.addEventListener('click', (e) => {
    e.preventDefault();
    (menu.hidden) ? open() : close();
  });

  // acessibilidade: fechar com Esc
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !menu.hidden) close();
  });

  // Sanitizar cabeçalhos: remover textos "Filtrar ..." se existirem
  document.querySelectorAll('table thead th').forEach(th => {
    const text = th.textContent.trim();
    if (/^Filtrar\s+/.test(text)) {
      // mantém apenas o título principal se houver span com .th-title; caso contrário,
      // remove o prefixo "Filtrar ...".
      const titleEl = th.querySelector('.th-title');
      if (titleEl) {
        th.childNodes.forEach(n => { if (n.nodeType === Node.TEXT_NODE) n.textContent = ''; });
      } else {
        th.textContent = text.replace(/^Filtrar\s+“?.+?”?\s*/i, '').trim();
      }
    }
  });
})();
