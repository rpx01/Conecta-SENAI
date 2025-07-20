function mostrarAlerta(msg, tipo='success') {
  const div = document.createElement('div');
  div.className = `alert alert-${tipo} alert-dismissible`;
  div.innerHTML = `${msg}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
  document.getElementById('alertContainer').appendChild(div);
}

async function carregarTreinamentos() {
  const tbody = document.getElementById('tabela-catalogo');
  tbody.innerHTML = '<tr><td colspan="5">Carregando...</td></tr>';
  try {
    const dados = await chamarAPI('/user/treinamentos');
    tbody.innerHTML = '';
    if (!Array.isArray(dados) || !dados.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum treinamento cadastrado.</td></tr>';
      return;
    }
    dados.forEach(t => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${t.nome}</td><td>${t.codigo||''}</td><td>${t.carga_horaria}h</td><td>${t.max_alunos}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary me-1" data-edit="${t.id}"><i class="bi bi-pencil"></i></button>
          <button class="btn btn-sm btn-outline-danger" data-del="${t.id}"><i class="bi bi-trash"></i></button>
        </td>`;
      tbody.appendChild(tr);
    });
  } catch(e){
    tbody.innerHTML = '<tr><td colspan="5" class="text-danger text-center">Erro ao carregar treinamentos.</td></tr>';
  }
}

let modal; let form; let treinamentoId;

document.addEventListener('DOMContentLoaded', () => {
  modal = new bootstrap.Modal(document.getElementById('modalTreinamento'));
  form = document.getElementById('formTreinamento');
  document.getElementById('btnNovo').addEventListener('click', () => abrirModal());
  document.getElementById('tabela-catalogo').addEventListener('click', cliqueTabela);
  form.addEventListener('submit', salvarTreinamento);
  carregarTreinamentos();
});

function abrirModal(data={}) {
  document.getElementById('modalTitle').textContent = data.id ? 'Editar Treinamento' : 'Novo Treinamento';
  treinamentoId = data.id || '';
  document.getElementById('treinamentoId').value = treinamentoId;
  document.getElementById('nome').value = data.nome || '';
  document.getElementById('codigo').value = data.codigo || '';
  document.getElementById('carga_horaria').value = data.carga_horaria || '';
  document.getElementById('max_alunos').value = data.max_alunos || 20;
  document.getElementById('materiais').value = (data.materiais_didaticos||[]).map(m=>m.url).join('\n');
  modal.show();
}

async function cliqueTabela(e){
  const id = e.target.closest('button')?.dataset.edit || e.target.closest('button')?.dataset.del;
  if(!id) return;
  if(e.target.closest('[data-edit]')){
    const resp = await chamarAPI(`/user/treinamentos/${id}`, 'GET');
    abrirModal(resp);
  } else if(e.target.closest('[data-del]')){
    if(confirm('Excluir este treinamento?')){
      await chamarAPI(`/user/treinamentos/${id}`, 'DELETE');
      mostrarAlerta('Treinamento excluído com sucesso');
      carregarTreinamentos();
    }
  }
}

async function salvarTreinamento(evt){
  evt.preventDefault();
  const dados = {
    nome: document.getElementById('nome').value,
    codigo: document.getElementById('codigo').value || null,
    carga_horaria: parseInt(document.getElementById('carga_horaria').value,10),
    max_alunos: parseInt(document.getElementById('max_alunos').value,10),
    materiais: document.getElementById('materiais').value.split(/\n+/).filter(Boolean).map(url => ({url}))
  };
  const metodo = treinamentoId ? 'PUT' : 'POST';
  const url = treinamentoId ? `/user/treinamentos/${treinamentoId}` : '/user/treinamentos';
  try {
    await chamarAPI(url, metodo, dados);
    modal.hide();
    mostrarAlerta('Treinamento salvo com sucesso');
    carregarTreinamentos();
  } catch {
    mostrarAlerta('Erro ao salvar', 'danger');
  }
}
