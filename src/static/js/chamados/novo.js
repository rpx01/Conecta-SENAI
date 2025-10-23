const API_BASE = '/api/chamados';
const MAX_FILES = 5;
const MAX_FILE_SIZE = 10 * 1024 * 1024;

function getAuthHeaders() {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchBase(resource) {
  const resp = await fetch(`${API_BASE}/base/${resource}`, { headers: getAuthHeaders() });
  if (!resp.ok) {
    throw new Error(`Falha ao carregar ${resource}`);
  }
  return resp.json();
}

function popularSelect(select, dados, textKey = 'nome') {
  select.innerHTML = '<option value="">Selecione</option>';
  dados.forEach((item) => {
    if (item.ativo === false) {
      return;
    }
    const option = document.createElement('option');
    option.value = item.id;
    option.textContent = item[textKey];
    select.appendChild(option);
  });
}

async function carregarDadosBase() {
  try {
    const [categorias, prioridades, locais, ativos] = await Promise.all([
      fetchBase('categorias'),
      fetchBase('prioridades'),
      fetchBase('locations'),
      fetchBase('assets'),
    ]);
    popularSelect(document.querySelector('#categoria'), categorias);
    popularSelect(document.querySelector('#prioridade'), prioridades);
    popularSelect(document.querySelector('#local'), locais);
    popularSelect(document.querySelector('#ativo'), ativos, 'tag');
  } catch (err) {
    document.querySelector('#status').textContent = err.message;
  }
}

function validarArquivos(files) {
  if (files.length > MAX_FILES) {
    throw new Error(`Máximo de ${MAX_FILES} arquivos permitido`);
  }
  Array.from(files).forEach((file) => {
    if (file.size > MAX_FILE_SIZE) {
      throw new Error(`Arquivo ${file.name} ultrapassa 10MB`);
    }
  });
}

async function enviarChamado(event) {
  event.preventDefault();
  const statusEl = document.querySelector('#status');
  statusEl.textContent = '';
  const form = event.target;
  try {
    if (form.titulo.value.trim().length < 3) {
      throw new Error('Informe um título válido');
    }
    if (form.descricao.value.trim().length < 10) {
      throw new Error('A descrição deve ter ao menos 10 caracteres');
    }
    validarArquivos(form.anexos.files);
    const dados = new FormData(form);
    const resp = await fetch(API_BASE, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: dados,
    });
    if (!resp.ok) {
      const erro = await resp.json().catch(() => ({}));
      throw new Error(erro.erro || 'Erro ao criar chamado');
    }
    const ticket = await resp.json();
    statusEl.textContent = `Chamado #${ticket.id} criado com sucesso!`;
    form.reset();
  } catch (err) {
    statusEl.textContent = err.message;
  }
}

window.addEventListener('DOMContentLoaded', () => {
  carregarDadosBase();
  document.querySelector('#form-chamado').addEventListener('submit', enviarChamado);
});
