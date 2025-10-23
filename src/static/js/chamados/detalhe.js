const API_BASE = '/api/chamados';
const POLLING_INTERVAL = 30000;

function getAuthHeaders(extra = {}) {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

function obterTicketId() {
  const partes = window.location.pathname.split('/').filter(Boolean);
  return partes[partes.length - 1];
}

async function fetchTicket() {
  const id = obterTicketId();
  const resp = await fetch(`${API_BASE}/${id}`, { headers: getAuthHeaders() });
  if (!resp.ok) {
    throw new Error('Não foi possível carregar o chamado');
  }
  return resp.json();
}

function renderTicket(ticket) {
  document.querySelector('#ticket-id').textContent = `#${ticket.id}`;
  const artigo = document.querySelector('#ticket');
  artigo.innerHTML = `
    <p><strong>Título:</strong> ${ticket.titulo}</p>
    <p><strong>Status:</strong> ${ticket.status_nome || ''}</p>
    <p><strong>Prioridade:</strong> ${ticket.prioridade_nome || ''}</p>
    <p><strong>Categoria:</strong> ${ticket.categoria_nome || ''}</p>
    <p><strong>Descrição:</strong> ${ticket.descricao}</p>
    <p><strong>Prazo SLA:</strong> ${ticket.prazo_sla ? new Date(ticket.prazo_sla).toLocaleString() : '-'}</p>
  `;
  const comentarios = document.querySelector('#comentarios');
  comentarios.innerHTML = '';
  ticket.comentarios.forEach((comentario) => {
    const li = document.createElement('li');
    li.textContent = `${comentario.autor_nome || 'Usuário'}: ${comentario.mensagem}`;
    comentarios.appendChild(li);
  });
  const anexos = document.querySelector('#anexos');
  anexos.innerHTML = '';
  ticket.anexos.forEach((anexo) => {
    const li = document.createElement('li');
    const link = document.createElement('a');
    link.href = `${API_BASE}/${ticket.id}/download/${anexo.id}`;
    link.textContent = `${anexo.filename} (${(anexo.size_bytes / 1024).toFixed(1)} KB)`;
    link.setAttribute('target', '_blank');
    li.appendChild(link);
    anexos.appendChild(li);
  });
}

async function enviarComentario(event) {
  event.preventDefault();
  const mensagem = document.querySelector('#mensagem').value.trim();
  if (!mensagem) {
    return;
  }
  const id = obterTicketId();
  const resp = await fetch(`${API_BASE}/${id}/comentarios`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ mensagem }),
  });
  if (!resp.ok) {
    alert('Erro ao enviar comentário');
    return;
  }
  document.querySelector('#mensagem').value = '';
  carregarTicket();
}

async function enviarAnexos(event) {
  event.preventDefault();
  const arquivos = document.querySelector('#novos-anexos').files;
  if (!arquivos.length) {
    return;
  }
  const dados = new FormData();
  Array.from(arquivos).forEach((file) => dados.append('anexos', file));
  const id = obterTicketId();
  const resp = await fetch(`${API_BASE}/${id}/anexos`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: dados,
  });
  if (!resp.ok) {
    alert('Erro ao enviar anexos');
    return;
  }
  document.querySelector('#novos-anexos').value = '';
  carregarTicket();
}

let pollingTimer = null;

async function carregarTicket() {
  try {
    const ticket = await fetchTicket();
    renderTicket(ticket);
  } catch (err) {
    console.error(err);
  }
}

window.addEventListener('DOMContentLoaded', () => {
  carregarTicket();
  pollingTimer = setInterval(carregarTicket, POLLING_INTERVAL);
  document.querySelector('#form-comentario').addEventListener('submit', enviarComentario);
  document.querySelector('#form-anexos').addEventListener('submit', enviarAnexos);
});

window.addEventListener('beforeunload', () => {
  if (pollingTimer) {
    clearInterval(pollingTimer);
  }
});
