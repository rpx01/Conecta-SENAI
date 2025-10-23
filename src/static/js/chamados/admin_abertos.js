const API_BASE = '/api/chamados';
let statusLista = [];
let paginaAtual = 1;

function getAuthHeaders(extra = {}) {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

async function fetchJSON(url, options = {}) {
  const resp = await fetch(url, { ...options, headers: getAuthHeaders(options.headers || {}) });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.erro || 'Erro na operação');
  }
  return resp.json();
}

async function carregarFiltros() {
  const [categorias, prioridades, statuses] = await Promise.all([
    fetchJSON(`${API_BASE}/base/categorias`),
    fetchJSON(`${API_BASE}/base/prioridades`),
    fetchJSON(`${API_BASE}/base/statuses`),
  ]);
  statusLista = statuses;
  preencherSelect(document.querySelector('#filtro-categoria'), categorias);
  preencherSelect(document.querySelector('#filtro-prioridade'), prioridades);
  preencherSelect(document.querySelector('#filtro-status'), statuses);
}

function preencherSelect(select, dados) {
  select.innerHTML = '<option value="">Todos</option>';
  dados.forEach((item) => {
    const option = document.createElement('option');
    option.value = item.id;
    option.textContent = item.nome;
    select.appendChild(option);
  });
}

async function carregarTabela() {
  const params = new URLSearchParams({ page: paginaAtual.toString(), page_size: '10' });
  ['status', 'categoria', 'prioridade'].forEach((campo) => {
    const select = document.querySelector(`#filtro-${campo}`);
    if (select.value) params.append(`${campo}_id`, select.value);
  });
  const atribuido = document.querySelector('#filtro-atribuido').value;
  if (atribuido) params.append('atribuido_id', atribuido);
  const busca = document.querySelector('#busca').value.trim();
  if (busca) params.append('q', busca);
  const resultado = await fetchJSON(`${API_BASE}/abertos?${params.toString()}`);
  renderTabela(resultado.items);
}

function renderTabela(itens) {
  const tbody = document.querySelector('#tabela-abertos tbody');
  tbody.innerHTML = '';
  itens.forEach((item) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${item.id}</td>
      <td><a href="/chamados/${item.id}">${item.titulo}</a></td>
      <td>${item.status_nome || ''}</td>
      <td>${item.prioridade_nome || ''}</td>
      <td>${item.solicitante_nome || ''}</td>
      <td>${item.atribuido_nome || '-'}</td>
      <td>
        <button data-id="${item.id}" class="btn-atribuir">Atribuir</button>
        <button data-id="${item.id}" class="btn-status">Status</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function atribuirChamado(id) {
  const usuarioId = prompt('Informe o ID do responsável');
  if (!usuarioId) return;
  await fetchJSON(`${API_BASE}/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ atribuido_id: Number(usuarioId) }),
  });
  carregarTabela();
}

async function alterarStatus(id) {
  const statusId = prompt(
    `Informe o ID do novo status\n${statusLista.map((s) => `${s.id} - ${s.nome}`).join('\n')}`
  );
  if (!statusId) return;
  await fetchJSON(`${API_BASE}/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status_id: Number(statusId) }),
  });
  carregarTabela();
}

window.addEventListener('DOMContentLoaded', async () => {
  await carregarFiltros();
  await carregarTabela();
  document.querySelector('#btn-aplicar').addEventListener('click', (event) => {
    event.preventDefault();
    paginaAtual = 1;
    carregarTabela();
  });
  document.querySelector('#tabela-abertos').addEventListener('click', (event) => {
    if (event.target.matches('.btn-atribuir')) {
      atribuirChamado(event.target.dataset.id);
    }
    if (event.target.matches('.btn-status')) {
      alterarStatus(event.target.dataset.id);
    }
  });
});
