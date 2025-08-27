/* global bootstrap, chamarAPI, showToast, escapeHTML, executarAcaoComFeedback */

// Mapeamento de tipos para os nomes que aparecem na interface
const NOMES_TIPO = {
    'treinamento': 'Treinamento',
    'publico-alvo': 'Público Alvo',
    'local': 'Local',
    'modalidade': 'Modalidade',
    'horario': 'Horário',
    'cargahoraria': 'Carga Horária',
    'instrutor': 'Instrutor'
};

// Variáveis globais para os modais e dados
let geralModal;
let instrutorModal;
let confirmacaoModal;
let itemParaExcluir = { id: null, tipo: null };

/**
 * Função principal que é executada quando o DOM está pronto.
 */
document.addEventListener('DOMContentLoaded', function () {
    // Inicializa os modais do Bootstrap
    geralModal = new bootstrap.Modal(document.getElementById('geralModal'));
    instrutorModal = new bootstrap.Modal(document.getElementById('instrutorModal'));
    confirmacaoModal = new bootstrap.Modal(document.getElementById('confirmacaoModal'));
    
    // Adiciona os listeners (ouvintes de eventos) aos botões de salvar e confirmar
    document.getElementById('btnSalvarGeral').addEventListener('click', salvarItemGeral);
    const formInstrutor = document.getElementById('formInstrutor');
    formInstrutor.addEventListener('submit', (e) => {
        e.preventDefault();
        salvarInstrutor();
    });
    document.getElementById('btnSalvarInstrutor').addEventListener('click', salvarInstrutor);
    document.getElementById('btnConfirmarExclusao').addEventListener('click', executarExclusao);

    // Carrega todos os dados iniciais das tabelas
    carregarTodosOsDados();
});

/**
 * Carrega os dados de todas as tabelas da página.
 */
async function carregarTodosOsDados() {
    const tipos = ['treinamento', 'instrutor', 'publico-alvo', 'local', 'modalidade', 'horario', 'cargahoraria'];

    // Itera sobre cada tipo e carrega os dados da sua respectiva tabela
    for (const tipo of tipos) {
        let endpoint = `/planejamento-basedados/${tipo}`;
        if (tipo === 'instrutor') {
            endpoint = '/instrutores'; // Endpoint específico para instrutores
        } else if (tipo === 'horario') {
            endpoint = '/horarios';
        }
        
        try {
            const dados = await chamarAPI(endpoint);
            renderizarTabela(tipo, dados);
        } catch (error) {
            console.error(`Falha ao carregar ${tipo}:`, error);
            showToast(`Não foi possível carregar dados de ${NOMES_TIPO[tipo]}.`, 'danger');
        }
    }
}

/**
 * Renderiza uma tabela específica com os dados fornecidos.
 * @param {string} tipo - O tipo de dados (ex: 'local', 'modalidade').
 * @param {Array} dados - O array de objetos para popular a tabela.
 */
function renderizarTabela(tipo, dados) {
    const tbody = document.getElementById(`tabela-${tipo}`);
    if (!tbody) return;

    tbody.innerHTML = ''; // Limpa o conteúdo atual da tabela
    if (!dados || dados.length === 0) {
        const colSpan = tipo === 'treinamento' || tipo === 'horario' ? 3 : 2;
        tbody.innerHTML = `<tr><td colspan="${colSpan}" class="text-center">Nenhum item cadastrado.</td></tr>`;
        return;
    }

    // Cria as linhas da tabela com os botões de editar e excluir
    dados.forEach(item => {
        const tr = document.createElement('tr');
        if (tipo === 'treinamento') {
            tr.innerHTML = `
                <td>${escapeHTML(item.nome)}</td>
                <td>${item.carga_horaria ?? ''}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary" onclick="editarItem('${tipo}', ${item.id}, '${escapeHTML(item.nome)}', ${item.carga_horaria ?? 'null'})">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="confirmarExclusao('${tipo}', ${item.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
        } else if (tipo === 'horario') {
            tr.innerHTML = `
                <td>${escapeHTML(item.nome)}</td>
                <td>${escapeHTML(item.turno ?? '')}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary" onclick="editarItem('${tipo}', ${item.id}, '${escapeHTML(item.nome)}', '', '${item.turno || ''}')">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="confirmarExclusao('${tipo}', ${item.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
        } else {
            tr.innerHTML = `
                <td>${escapeHTML(item.nome)}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary" onclick="editarItem('${tipo}', ${item.id}, '${escapeHTML(item.nome)}')">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="confirmarExclusao('${tipo}', ${item.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
        }
        tbody.appendChild(tr);
    });
}

/**
 * Abre o modal genérico para adicionar ou editar um item.
 * @param {string} tipo - O tipo de item a ser adicionado/editado.
 * @param {number|null} id - O ID do item (para edição).
 * @param {string|null} nome - O nome atual do item (para edição).
 */
window.abrirModal = (tipo, id = null, nome = '', carga = '', turno = '') => {
    const form = document.getElementById('geralForm');
    form.reset();
    document.getElementById('itemType').value = tipo;
    document.getElementById('itemId').value = id || '';
    document.getElementById('itemName').value = nome || '';
    const turnoGroup = document.getElementById('turnoGroup');
    const selectTurno = document.getElementById('turnoHorario');
    if (tipo === 'horario') {
        turnoGroup.classList.remove('d-none');
        selectTurno.value = turno || '';
    } else {
        turnoGroup.classList.add('d-none');
        selectTurno.value = '';
    }

    const cargaGroup = document.getElementById('cargaHorariaGroup');
    const cargaInput = document.getElementById('itemCargaHoraria');
    if (tipo === 'treinamento') {
        cargaGroup.classList.remove('d-none');
        cargaInput.value = carga || '';
    } else {
        cargaGroup.classList.add('d-none');
        cargaInput.value = '';
    }
    
    const modalLabel = document.getElementById('geralModalLabel');
    modalLabel.textContent = `${id ? 'Editar' : 'Adicionar'} ${NOMES_TIPO[tipo]}`;
    
    geralModal.show();
};

// Disponibiliza a função no escopo global para ser chamada pelo HTML
window.editarItem = window.abrirModal;

/**
 * Abre o modal de instrutor para adicionar um novo instrutor.
 */
window.abrirModalInstrutor = () => {
    document.getElementById('formInstrutor').reset();
    document.getElementById('instrutorId').value = '';
    carregarAreasInstrutor();
    instrutorModal.show();
};

/**
 * Salva um item genérico (chama a API para criar ou atualizar).
 */
async function salvarItemGeral() {
    const form = document.getElementById('geralForm');
    const tipo = document.getElementById('itemType').value;
    const id = document.getElementById('itemId').value;
    const nome = document.getElementById('itemName').value.trim();
    const cargaHoraria = document.getElementById('itemCargaHoraria').value;
    const turno = document.querySelector('#turnoHorario')?.value || '';

    if (!nome) {
        showToast('O nome não pode estar vazio.', 'warning');
        return;
    }
    if (tipo === 'horario' && !turno) {
        showToast('Selecione um turno.', 'warning');
        return;
    }

    const method = id ? 'PUT' : 'POST';

    if (tipo === 'horario') {
        await salvarHorario(id, nome, turno);
        return;
    }

    let endpoint = id
        ? `/planejamento-basedados/${tipo}/${id}`
        : `/planejamento-basedados/${tipo}`;

    const payload = { nome };
    if (tipo === 'treinamento' && cargaHoraria) {
        payload.carga_horaria = parseInt(cargaHoraria, 10);
    }

    try {
        await chamarAPI(endpoint, method, payload);
        showToast(`${NOMES_TIPO[tipo]} ${id ? 'atualizado' : 'adicionado'} com sucesso!`, 'success');
        geralModal.hide();
        carregarTodosOsDados(); // Recarrega os dados para atualizar a tabela
    } catch (error) {
        showToast(error.message, 'danger');
    }
}

async function salvarHorario(id, nome, turno) {
    const endpoint = id ? `/horarios/${id}` : '/horarios';
    const method = id ? 'PUT' : 'POST';
    try {
        await executarAcaoComFeedback(
            document.getElementById('btnSalvarGeral'),
            async () => {
                await chamarAPI(endpoint, method, { nome, turno });
            }
        );
        showToast(`${NOMES_TIPO['horario']} ${id ? 'atualizado' : 'adicionado'} com sucesso!`, 'success');
        geralModal.hide();
        carregarTodosOsDados();
    } catch (error) {
        showToast(error.message || 'Erro ao salvar horário', 'danger');
    }
}

/**
 * Busca as áreas de atuação para o formulário de instrutor.
 */
async function carregarAreasInstrutor() {
    try {
        const areas = await chamarAPI('/instrutores/areas-atuacao');
        const select = document.getElementById('instrutorArea');
        if (!select) return;
        select.innerHTML = '<option value="">Selecione...</option>';
        areas.forEach(a => {
            const opt = document.createElement('option');
            opt.value = a.valor;
            opt.textContent = a.nome;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error('Erro ao carregar áreas de atuação', err);
    }
}

/**
 * Salva um instrutor (chama a API para criar ou atualizar).
 */
async function salvarInstrutor() {
    const id = document.getElementById('instrutorId').value;
    const nome = document.getElementById('instrutorNome').value.trim();
    const email = document.getElementById('instrutorEmail').value.trim();
    const area_atuacao = document.getElementById('instrutorArea').value;
    const status = document.getElementById('instrutorStatus').value;
    const observacoes = document.getElementById('instrutorObservacoes').value.trim();
    const disponibilidade = [];
    if (document.getElementById('dispManha').checked) disponibilidade.push('manha');
    if (document.getElementById('dispTarde').checked) disponibilidade.push('tarde');
    if (document.getElementById('dispNoite').checked) disponibilidade.push('noite');

    if (!nome || !email) {
        showToast('Nome e e-mail são obrigatórios.', 'warning');
        return;
    }

    const dados = { nome, email, area_atuacao, status, observacoes, disponibilidade };
    const endpoint = id ? `/instrutores/${id}` : '/instrutores';
    const method = id ? 'PUT' : 'POST';

    try {
        await chamarAPI(endpoint, method, dados);
        showToast(`Instrutor ${id ? 'atualizado' : 'adicionado'} com sucesso!`, 'success');
        instrutorModal.hide();
        carregarTodosOsDados();
    } catch (error) {
        showToast(error.message, 'danger');
    }
}

/**
 * Prepara e abre o modal para confirmar a exclusão de um item.
 * @param {string} tipo - O tipo de item a ser excluído.
 * @param {number} id - O ID do item a ser excluído.
 */
window.confirmarExclusao = (tipo, id) => {
    itemParaExcluir = { tipo, id };
    confirmacaoModal.show();
};

/**
 * Executa a exclusão após a confirmação do usuário.
 */
async function executarExclusao() {
    const { tipo, id } = itemParaExcluir;
    if (!tipo || !id) return;
    
    let endpoint = `/planejamento-basedados/${tipo}/${id}`;
    if (tipo === 'instrutor') {
        endpoint = `/instrutores/${id}`;
    } else if (tipo === 'horario') {
        endpoint = `/horarios/${id}`;
    }

    try {
        await chamarAPI(endpoint, 'DELETE');
        showToast('Item excluído com sucesso!', 'success');
        carregarTodosOsDados(); // Recarrega os dados para atualizar a tabela
    } catch (error) {
        showToast(error.message, 'danger');
    } finally {
        confirmacaoModal.hide();
        itemParaExcluir = { id: null, tipo: null };
    }
}

