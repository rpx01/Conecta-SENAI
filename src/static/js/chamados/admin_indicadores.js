const API_BASE = '/api/chamados/indicadores';

function getAuthHeaders() {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function carregarIndicadores() {
  const periodo = document.querySelector('#periodo').value || 30;
  const resp = await fetch(`${API_BASE}?periodo=${periodo}`, { headers: getAuthHeaders() });
  if (!resp.ok) {
    alert('Falha ao carregar indicadores');
    return;
  }
  const dados = await resp.json();
  renderIndicadores(dados);
}

function renderIndicadores(dados) {
  const sla = document.querySelector('#sla');
  sla.textContent = `SLA: ${dados.sla.dentro} dentro / ${dados.sla.fora} fora`;
  const tmr = document.querySelector('#tmr');
  tmr.textContent = `Tempo médio de resolução: ${dados.media_resolucao_horas} horas`;
  const envelhecimento = document.querySelector('#envelhecimento');
  envelhecimento.innerHTML = '<h3>Backlog por idade</h3>' +
    Object.entries(dados.envelhecimento || {})
      .map(([faixa, total]) => `<div>${faixa} dias: ${total}</div>`)
      .join('');
  desenharGrafico(document.querySelector('#chart-status'), dados.por_status, 'Status');
  desenharGrafico(document.querySelector('#chart-categoria'), dados.por_categoria, 'Categoria');
  desenharGrafico(document.querySelector('#chart-prioridade'), dados.por_prioridade, 'Prioridade');
}

function desenharGrafico(canvas, dataset, titulo) {
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const entries = Object.entries(dataset || {});
  if (!entries.length) {
    ctx.fillText('Sem dados', 10, 20);
    return;
  }
  const total = Math.max(...entries.map(([, valor]) => valor));
  const barWidth = (canvas.width - 40) / entries.length;
  ctx.fillStyle = '#004b8d';
  ctx.font = '14px sans-serif';
  ctx.fillText(titulo, 10, 20);
  entries.forEach(([label, valor], index) => {
    const altura = total ? (valor / total) * (canvas.height - 60) : 0;
    const x = 20 + index * barWidth;
    const y = canvas.height - altura - 20;
    ctx.fillRect(x, y, barWidth - 10, altura);
    ctx.fillText(label, x, canvas.height - 5);
    ctx.fillText(String(valor), x, y - 5);
  });
}

window.addEventListener('DOMContentLoaded', () => {
  document.querySelector('#btn-carregar').addEventListener('click', carregarIndicadores);
  carregarIndicadores();
});
