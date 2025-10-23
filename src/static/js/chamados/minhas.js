const API_BASE = '/api/chamados';

function getAuthHeaders() {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchJSON(url) {
  const resp = await fetch(url, { headers: getAuthHeaders() });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.erro || 'Erro na requisição');
  }
  return resp.json();
}

async function carregarFiltros() {
  const [categorias, prioridades, statuses] = await Promise.all([
    fetchJSON(`${API_BASE}/base/categorias`),
    fetchJSON(`${API_BASE}/base/prioridades`),
    fetchJSON(`${API_BASE}/base/statuses`),
  ]);
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

let paginaAtual = 1;

async function carregarChamados() {
  const params = new URLSearchParams({ mine: 'true', page: paginaAtual.toString(), page_size: '10' });
  const status = document.querySelector('#filtro-status').value;
  const categoria = document.querySelector('#filtro-categoria').value;
  const prioridade = document.querySelector('#filtro-prioridade').value;
  const busca = document.querySelector('#busca').value.trim();
  if (status) params.append('status_id', status);
  if (categoria) params.append('categoria_id', categoria);
  if (prioridade) params.append('prioridade_id', prioridade);
  if (busca) params.append('q', busca);
  const resultado = await fetchJSON(`${API_BASE}?${params.toString()}`);
  atualizarTabela(resultado.items);
  document.querySelector('#pagina-atual').textContent = `${resultado.page}/${resultado.pages || 1}`;
  document.querySelector('#prev').disabled = resultado.page <= 1;
  document.querySelector('#next').disabled = resultado.page >= (resultado.pages || 1);
}

function atualizarTabela(itens) {
  const tbody = document.querySelector('#tabela-chamados tbody');
  tbody.innerHTML = '';
  itens.forEach((item) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${item.id}</td>
      <td><a href="/chamados/${item.id}">${item.titulo}</a></td>
      <td>${item.status_nome || ''}</td>
      <td>${item.prioridade_nome || ''}</td>
      <td>${new Date(item.updated_at || item.created_at).toLocaleString()}</td>
    `;
    tbody.appendChild(tr);
  });
}

window.addEventListener('DOMContentLoaded', async () => {
  await carregarFiltros();
  await carregarChamados();
  document.querySelector('#btn-filtrar').addEventListener('click', (event) => {
    event.preventDefault();
    paginaAtual = 1;
    carregarChamados();
  });
  document.querySelector('#prev').addEventListener('click', () => {
    if (paginaAtual > 1) {
      paginaAtual -= 1;
      carregarChamados();
    }
  });
  document.querySelector('#next').addEventListener('click', () => {
    paginaAtual += 1;
    carregarChamados();
  });
});
