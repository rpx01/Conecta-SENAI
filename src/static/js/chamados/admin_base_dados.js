const API_BASE = '/api/chamados/base';
const recursos = ['categorias', 'prioridades', 'statuses', 'locations', 'assets', 'slas'];

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
  return resp.json().catch(() => ({}));
}

async function carregarRecurso(recurso) {
  const dados = await fetchJSON(`${API_BASE}/${recurso}`);
  const container = document.querySelector(`#${recurso} .lista`);
  container.innerHTML = '';
  dados.forEach((item) => {
    const li = document.createElement('li');
    li.textContent = JSON.stringify(item);
    const btnEditar = document.createElement('button');
    btnEditar.textContent = 'Editar';
    btnEditar.addEventListener('click', () => editarRecurso(recurso, item.id));
    const btnExcluir = document.createElement('button');
    btnExcluir.textContent = 'Excluir';
    btnExcluir.addEventListener('click', () => excluirRecurso(recurso, item.id));
    li.appendChild(btnEditar);
    li.appendChild(btnExcluir);
    container.appendChild(li);
  });
}

async function criarRecurso(event) {
  event.preventDefault();
  const form = event.target;
  const recurso = form.dataset.resource;
  const dados = Object.fromEntries(new FormData(form).entries());
  try {
    await fetchJSON(`${API_BASE}/${recurso}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    });
    form.reset();
    carregarRecurso(recurso);
  } catch (err) {
    alert(err.message);
  }
}

async function editarRecurso(recurso, id) {
  const novoValor = prompt('Informe os dados no formato chave=valor separados por vírgula');
  if (!novoValor) return;
  const dados = {};
  novoValor.split(',').forEach((par) => {
    const [chave, valor] = par.split('=').map((p) => p.trim());
    if (chave) dados[chave] = valor;
  });
  await fetchJSON(`${API_BASE}/${recurso}/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dados),
  });
  carregarRecurso(recurso);
}

async function excluirRecurso(recurso, id) {
  if (!confirm('Deseja realmente excluir?')) return;
  const resp = await fetch(`${API_BASE}/${recurso}/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (resp.status === 204) {
    carregarRecurso(recurso);
  } else {
    const body = await resp.json().catch(() => ({}));
    alert(body.erro || 'Não foi possível excluir');
  }
}

window.addEventListener('DOMContentLoaded', () => {
  recursos.forEach((recurso) => {
    document
      .querySelector(`#${recurso} form`)
      .addEventListener('submit', criarRecurso);
    carregarRecurso(recurso);
  });
});
