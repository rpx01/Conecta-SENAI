let modalCadastro;
let tipoCadastroAtual = 'area';
let idEdicaoAtual = null;
let areasCache = [];
let equipamentosCache = [];

async function carregarListas() {
    await Promise.all([renderizarAreas(), renderizarEquipamentos()]);
}

async function renderizarAreas() {
    const tbody = document.querySelector('#tabelaAreas tbody');
    try {
        const areas = await window.__suporteTI.carregarAreas({ incluirInativas: true });
        areasCache = areas;
        if (!areas.length) {
            tbody.innerHTML = '<tr><td colspan="2" class="text-center py-3 text-muted">Nenhuma área cadastrada.</td></tr>';
            return;
        }
        tbody.innerHTML = areas.map(area => `
            <tr data-id="${area.id}" data-tipo="area">
                <td>
                    <strong>${escapeHTML(area.nome)}</strong>
                    ${area.descricao ? `<div class="text-muted small">${escapeHTML(area.descricao)}</div>` : ''}
                    ${area.ativo ? '' : '<span class="badge bg-secondary mt-1">Inativa</span>'}
                </td>
                <td class="text-end">
                    <button class="btn btn-outline-primary btn-sm" data-action="editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-danger btn-sm" data-action="excluir">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>`).join('');
    } catch (erro) {
        console.error('Erro ao carregar áreas', erro);
        tbody.innerHTML = '<tr><td colspan="2" class="text-center py-3 text-danger">Erro ao carregar áreas.</td></tr>';
    }
}

async function renderizarEquipamentos() {
    const tbody = document.querySelector('#tabelaEquipamentos tbody');
    try {
        const equipamentos = await window.__suporteTI.carregarEquipamentos({ incluirInativos: true });
        equipamentosCache = equipamentos;
        if (!equipamentos.length) {
            tbody.innerHTML = '<tr><td colspan="2" class="text-center py-3 text-muted">Nenhum tipo de equipamento cadastrado.</td></tr>';
            return;
        }
        tbody.innerHTML = equipamentos.map(eq => `
            <tr data-id="${eq.id}" data-tipo="equipamento">
                <td>
                    <strong>${escapeHTML(eq.nome)}</strong>
                    ${eq.descricao ? `<div class="text-muted small">${escapeHTML(eq.descricao)}</div>` : ''}
                    ${eq.ativo ? '' : '<span class="badge bg-secondary mt-1">Inativo</span>'}
                </td>
                <td class="text-end">
                    <button class="btn btn-outline-primary btn-sm" data-action="editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-danger btn-sm" data-action="excluir">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>`).join('');
    } catch (erro) {
        console.error('Erro ao carregar equipamentos', erro);
        tbody.innerHTML = '<tr><td colspan="2" class="text-center py-3 text-danger">Erro ao carregar equipamentos.</td></tr>';
    }
}

function abrirModalCadastro(tipo, registro = null) {
    tipoCadastroAtual = tipo;
    idEdicaoAtual = registro?.id ?? null;
    const titulo = tipo === 'area' ? 'Área de atendimento' : 'Tipo de equipamento';
    document.getElementById('modalCadastroLabel').textContent = idEdicaoAtual ? `Editar ${titulo}` : `Nova ${titulo.toLowerCase()}`;
    document.getElementById('inputNomeCadastro').value = registro?.nome || '';
    document.getElementById('inputDescricaoCadastro').value = registro?.descricao || '';
    document.getElementById('checkAtivo').checked = registro?.ativo !== false;
    document.getElementById('formCadastro').classList.remove('was-validated');
    if (!modalCadastro) {
        modalCadastro = new bootstrap.Modal(document.getElementById('modalCadastro'));
    }
    modalCadastro.show();
}

async function salvarCadastro(evento) {
    evento.preventDefault();
    const form = evento.currentTarget;
    form.classList.add('was-validated');
    if (!form.checkValidity()) {
        return;
    }
    const nome = document.getElementById('inputNomeCadastro').value.trim();
    const descricao = document.getElementById('inputDescricaoCadastro').value.trim();
    const ativo = document.getElementById('checkAtivo').checked;

    const payload = { nome, descricao, ativo };
    const endpointBase = tipoCadastroAtual === 'area' ? '/support/areas' : '/support/equipamentos';
    const metodo = idEdicaoAtual ? 'PUT' : 'POST';
    const endpoint = idEdicaoAtual ? `${endpointBase}/${idEdicaoAtual}` : endpointBase;
    const botaoSalvar = form.querySelector('button[type="submit"]');

    try {
        setBusy(botaoSalvar, true);
        await chamarAPI(endpoint, metodo, payload);
        showToast('Cadastro salvo com sucesso!', 'success');
        modalCadastro.hide();
        await carregarListas();
    } catch (erro) {
        console.error('Erro ao salvar cadastro', erro);
        const mensagem = erro?.message || 'Não foi possível salvar o cadastro.';
        showToast(mensagem, 'danger');
    } finally {
        setBusy(botaoSalvar, false);
    }
}

async function excluirRegistro(tipo, id) {
    if (!window.confirm('Confirma a exclusão deste registro?')) {
        return;
    }
    const endpointBase = tipo === 'area' ? '/support/areas' : '/support/equipamentos';
    try {
        await chamarAPI(`${endpointBase}/${id}`, 'DELETE');
        showToast('Registro removido com sucesso.', 'success');
        await carregarListas();
    } catch (erro) {
        console.error('Erro ao remover registro', erro);
        showToast('Não foi possível remover o registro.', 'danger');
    }
}

function configurarEventos() {
    document.getElementById('btnAdicionarArea')?.addEventListener('click', () => abrirModalCadastro('area'));
    document.getElementById('btnAdicionarEquipamento')?.addEventListener('click', () => abrirModalCadastro('equipamento'));
    document.getElementById('formCadastro')?.addEventListener('submit', salvarCadastro);

    document.addEventListener('click', evento => {
        const botao = evento.target.closest('button[data-action]');
        if (!botao) return;
        const linha = botao.closest('tr[data-id]');
        if (!linha) return;
        const tipo = linha.dataset.tipo;
        const id = Number(linha.dataset.id);
        const action = botao.dataset.action;
        const registro = (tipo === 'area'
            ? areasCache.find(area => area.id === id)
            : equipamentosCache.find(eq => eq.id === id)) || {
            id,
            nome: linha.querySelector('strong')?.textContent || '',
            descricao: linha.querySelector('.text-muted')?.textContent || '',
            ativo: !linha.querySelector('.badge')
        };
        if (action === 'editar') {
            abrirModalCadastro(tipo, registro);
        } else if (action === 'excluir') {
            excluirRegistro(tipo, id);
        }
    });
}

(async function init() {
    if (!(await verificarPermissaoAdmin())) return;
    configurarEventos();
    await carregarListas();
})();
