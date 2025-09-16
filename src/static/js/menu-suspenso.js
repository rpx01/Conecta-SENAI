(() => {
  const drawer = document.getElementById('sidebarDrawer');
  const edge   = document.getElementById('hoverEdge');
  if (!drawer || !edge) return;

  let openTimer, closeTimer;

  const open = () => {
    clearTimeout(closeTimer);
    drawer.classList.add('open');
    drawer.setAttribute('aria-expanded', 'true');
  };

  const close = () => {
    clearTimeout(openTimer);
    // só fecha se o mouse não estiver sobre o drawer
    if (!drawer.matches(':hover')) {
      drawer.classList.remove('open');
      drawer.setAttribute('aria-expanded', 'false');
    }
  };

  // Abrir ao encostar na borda
  edge.addEventListener('mouseenter', () => { openTimer = setTimeout(open, 80); });

  // Fechar ao sair do drawer (pequeno atraso para tolerar trajetos do mouse)
  drawer.addEventListener('mouseleave', () => { closeTimer = setTimeout(close, 150); });

  // Manter aberto enquanto houver foco de teclado dentro do drawer
  drawer.addEventListener('focusin', open);
  drawer.addEventListener('focusout', () => { setTimeout(close, 120); });

  // Suporte a toque / fallback sem hover: tocar/clicar na borda alterna o estado
  edge.addEventListener('click', () => {
    drawer.classList.toggle('open');
    const expanded = drawer.classList.contains('open');
    drawer.setAttribute('aria-expanded', expanded ? 'true' : 'false');
  });

  // Fecha com ESC
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') close();
  });
})();
