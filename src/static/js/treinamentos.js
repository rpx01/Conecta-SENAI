function initDeadlineCounters() {
  const CLOSE_AHEAD_MS = 36 * 60 * 60 * 1000; // 1 dia e 12 horas

  document.querySelectorAll('.card, .curso-card, [data-card-curso]').forEach(card => {
    const periodoEl = findByLabel(card, 'Período:') || card.querySelector('[data-periodo]');
    const horarioEl = findByLabel(card, 'Horário:') || card.querySelector('[data-horario]');
    const deadlineEl = card.querySelector('[data-deadline]') || findByLabel(card, 'Inscrições encerram');

    if (!periodoEl || !horarioEl || !deadlineEl) return;

    const brInicio = extrairPrimeiraDataBR(periodoEl.textContent);      // dd/mm/aaaa
    const hmInicio  = extrairPrimeiroHorario(horarioEl.textContent) || {h:8,m:0}; // fallback 08:00
    if (!brInicio) return;

    const inicio = criarDataLocal(brInicio, hmInicio.h, hmInicio.m);
    const deadline = new Date(inicio.getTime() - CLOSE_AHEAD_MS);

    function tick() {
      const agora = new Date();
      const diff = deadline - agora;

      if (diff <= 0) {
        deadlineEl.textContent = 'Inscrições encerradas';
        return;
      }
      const d = Math.floor(diff / 86400000);
      const h = Math.floor((diff % 86400000) / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);

      const restante = d >= 1 ? `${d}d e ${h}h` : `${h}h e ${m}min`;
      deadlineEl.textContent = `Inscrições encerram em: ${restante}`;
    }

    tick();
    setInterval(tick, 60000); // atualiza a cada 1 min
  });

  function extrairPrimeiraDataBR(txt) {
    const m = txt.match(/(\d{2}\/\d{2}\/\d{4})/);
    return m ? m[1] : null;
  }

  function extrairPrimeiroHorario(txt) {
    const m = txt.match(/(\d{2})\s*[Hh:\.]\s*(\d{2})/);
    if (!m) return null;
    return { h: parseInt(m[1], 10), m: parseInt(m[2], 10) };
  }

  function criarDataLocal(br, h, m) {
    const [d, mo, y] = br.split('/').map(Number);
    return new Date(y, mo - 1, d, h, m, 0, 0);
  }

  function findByLabel(root, startText) {
    const lower = startText.toLowerCase();
    return Array.from(root.querySelectorAll('li,div,span,small,p'))
      .find(el => el.textContent.trim().toLowerCase().startsWith(lower));
  }
}

document.addEventListener('DOMContentLoaded', initDeadlineCounters);
window.initDeadlineCounters = initDeadlineCounters;
