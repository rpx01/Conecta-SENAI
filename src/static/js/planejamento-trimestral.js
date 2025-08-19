/* global bootstrap, chamarAPI, showToast, escapeHTML */

// Mapeamento dos endpoints da API para os IDs dos selects no HTML
const mapeamentoSelects = {
    'itemHorario': '/planejamento-basedados/horario',
    'itemCargaHoraria': '/planejamento-basedados/cargahoraria',
    'itemModalidade': '/planejamento-basedados/modalidade',
    'itemTreinamento': '/planejamento-basedados/treinamento',
    'itemCmd': '/planejamento-basedados/publico-alvo',
    'itemSjb': '/planejamento-basedados/publico-alvo',
    'itemSagTombos': '/planejamento-basedados/publico-alvo',
    'itemInstrutor': '/instrutores',
    'itemLocal': '/planejamento-basedados/local',
};

let itemModal;
let confirmacaoModal;
let itemParaExcluirId = null;

/**
 * Função executada quando o DOM está totalmente carregado.
 */
document.addEventListener('DOMContentLoaded', async () => {
    itemModal = new bootstrap.Modal(document.getElementById('itemModal'));
    confirmacaoModal = new bootstrap.Modal(document.getElementById('confirmacaoModal'));

    document.getElementById('itemData').addEventListener('change', calcularSemana);
    document.getElementById('btnConfirmarExclusao').addEventListener('click', executarExclusao);

    document.getElementById('btn-adicionar-planejamento').addEventListener('click', () => abrirModalParaAdicionar());

    await inicializarPagina();
});

/**
 * Orquestra o carregamento inicial dos dados da página.
 */
async function inicializarPagina() {
    try {
        await Promise.all([
            carregarOpcoesDosSelects(),
            carregarItens()
        ]);
    } catch (error) {
        console.error("Erro ao inicializar a página:", error);
        showToast("Falha ao carregar dados iniciais da página.", 'danger');
    }
}

/**
 * Busca os dados da API e popula todos os campos de seleção do modal.
 */
async function carregarOpcoesDosSelects() {
    const promessas = Object.entries(mapeamentoSelects).map(async ([selectId, endpoint]) => {
        try {
            const dados = await chamarAPI(endpoint);
            popularSelect(selectId, dados);
        } catch (error) {
            console.error(`Falha ao carregar opções para ${selectId}:`, error);
            showToast(`Erro ao carregar dados para ${selectId.replace('item', '')}.`, 'warning');
        }
    });
    
    await Promise.all(promessas);
}

/**
 * Popula um elemento <select> com os dados fornecidos.
 */
function popularSelect(selectId, dados) {
    const select = document.getElementById(selectId);
    if (!select) return;

    const placeholder = select.options[0];
    select.innerHTML = '';
    select.appendChild(placeholder);

    dados.forEach(item => {
        const option = document.createElement('option');
        option.value = escapeHTML(item.nome);
        option.textContent = escapeHTML(item.nome);
        select.appendChild(option);
    });
}

/**
 * Calcula o número da semana com base na data selecionada.
 */
function calcularSemana() {
    const dataInput = document.getElementById('itemData').value;
    if (dataInput) {
        const data = new Date(dataInput + "T00:00:00");
        const primeiroDiaDoAno = new Date(data.getFullYear(), 0, 1);
        const diasPassados = Math.floor((data - primeiroDiaDoAno) / (24 * 60 * 60 * 1000));
        const semana = Math.ceil((data.getDay() + 1 + diasPassados) / 7);
        document.getElementById('itemSemana').value = `SEMANA ${semana}`;
    }
}

/**
 * Abre o modal para adicionar um novo item.
 */
window.abrirModalParaAdicionar = (loteId) => {
    document.getElementById('itemForm').reset();
    document.getElementById('itemId').value = '';
    document.getElementById('loteId').value = loteId;
    document.getElementById('itemModalLabel').textContent = 'Adicionar Item ao Planejamento';
    itemModal.show();
};

/**
 * Abre o modal para editar um item existente.
 */
window.abrirModalParaEditar = (item) => {
    document.getElementById('itemForm').reset();
    
    document.getElementById('itemId').value = item.id;
    document.getElementById('loteId').value = item.loteId;
    document.getElementById('itemData').value = item.data;
    document.getElementById('itemSemana').value = item.semana;
    document.getElementById('itemHorario').value = item.horario;
    document.getElementById('itemCargaHoraria').value = item.cargaHoraria;
    document.getElementById('itemModalidade').value = item.modalidade;
    document.getElementById('itemTreinamento').value = item.treinamento;
    document.getElementById('itemCmd').value = item.cmd;
    document.getElementById('itemSjb').value = item.sjb;
    document.getElementById('itemSagTombos').value = item.sagTombos;
    document.getElementById('itemInstrutor').value = item.instrutor;
    document.getElementById('itemLocal').value = item.local;
    document.getElementById('itemObservacao').value = item.observacao;

    document.getElementById('itemModalLabel').textContent = 'Editar Item do Planejamento';
    itemModal.show();
};

/**
 * Salva um item (cria um novo ou atualiza um existente).
 */
async function salvarItem() {
    const id = document.getElementById('itemId').value;
    const loteId = document.getElementById('loteId').value;
    
    const dados = {
        loteId: loteId,
        data: document.getElementById('itemData').value,
        semana: document.getElementById('itemSemana').value,
        horario: document.getElementById('itemHorario').value,
        carga_horaria: document.getElementById('itemCargaHoraria').value,
        modalidade: document.getElementById('itemModalidade').value,
        treinamento: document.getElementById('itemTreinamento').value,
        cmd: document.getElementById('itemCmd').value,
        sjb: document.getElementById('itemSjb').value,
        sag_tombos: document.getElementById('itemSagTombos').value,
        instrutor: document.getElementById('itemInstrutor').value,
        local: document.getElementById('itemLocal').value,
        observacao: document.getElementById('itemObservacao').value,
    };

    if (!dados.data || !dados.horario || !dados.treinamento) {
        showToast('Preencha todos os campos obrigatórios.', 'warning');
        return;
    }
    
    const endpoint = id ? `/planejamento/itens/${id}` : '/planejamento/itens';
    const method = id ? 'PUT' : 'POST';

    try {
        await chamarAPI(endpoint, method, dados);
        showToast(`Item ${id ? 'atualizado' : 'salvo'} com sucesso!`, 'success');
        itemModal.hide();
        await carregarItens();
    } catch (error) {
        showToast(error.message, 'danger');
    }
}

/**
 * Carrega e renderiza todos os itens do planejamento.
 */
async function carregarItens() {
    try {
        const itens = await chamarAPI('/planejamento/itens');
        renderizarLotes(itens);
    } catch (error) {
        showToast('Não foi possível carregar o planejamento.', 'danger');
    }
}

/**
 * Renderiza os lotes e os itens do planejamento na página.
 */
function renderizarLotes(itens) {
    const mainContainer = document.querySelector('main.col-lg-9');
    // The header containing the "Adicionar" button uses the CSS class
    // `page-header`. Previously, this code attempted to retrieve the
    // header using a combination of Bootstrap classes
    // `.d-flex.justify-content-between`, which no longer exist on the
    // element. As a result, the header (and consequently the add button)
    // was removed from the DOM when the main container was cleared,
    // leaving only the "Nenhum item de planejamento encontrado." message.
    //
    // To ensure the header is preserved regardless of styling changes,
    // we query it directly by its semantic `page-header` class.
    const header = mainContainer.querySelector('.page-header');
    mainContainer.innerHTML = ''; // Limpa o conteúdo
    if (header) {
        mainContainer.appendChild(header); // Readiciona o cabeçalho
    }

    const lotes = agruparItensPorLote(itens);

    if (Object.keys(lotes).length === 0) {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-striped table-hover mb-0">
                        ${criarCabecalhoTabela()}
                        <tbody>
                            <tr>
                                <td colspan="13" class="text-center">Nenhum item de planejamento encontrado.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>`;
        mainContainer.appendChild(card);
        return;
    }

    for (const loteId in lotes) {
        const itensDoLote = lotes[loteId];
        const primeiroItem = itensDoLote[0];
        const data = new Date(primeiroItem.data + 'T00:00:00');
        const ano = data.getFullYear();
        const trimestre = Math.floor(data.getMonth() / 3) + 1;

        const loteCard = document.createElement('div');
        loteCard.className = 'card mb-4';
        loteCard.innerHTML = `
            <div class="card-header d-flex justify-content-between align-items-center">
                <h2 class="h5 mb-0">${trimestre}º Trimestre de ${ano}</h2>
                <button class="btn btn-primary btn-sm" onclick="abrirModalParaAdicionar('${loteId}')">
                    <i class="bi bi-plus-circle me-1"></i> Adicionar Item
                </button>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-striped table-hover mb-0">
                        ${criarCabecalhoTabela()}
                        <tbody>
                            ${itensDoLote.map(item => criarLinhaItem(item)).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        mainContainer.appendChild(loteCard);
    }
}

/**
 * Agrupa os itens por lote (trimestre).
 */
function agruparItensPorLote(itens) {
    return itens.reduce((acc, item) => {
        (acc[item.loteId] = acc[item.loteId] || []).push(item);
        return acc;
    }, {});
}

/**
 * Cria o cabeçalho da tabela de itens.
 */
function criarCabecalhoTabela() {
    return `
        <thead>
            <tr>
                <th>Data</th><th>Semana</th><th>Horário</th><th>C.H.</th>
                <th>Modalidade</th><th>Treinamento</th><th>CMD</th><th>SJB</th>
                <th>SAG/TOMBOS</th><th>Instrutor</th><th>Local</th><th>Obs.</th>
                <th class="text-end">Ações</th>
            </tr>
        </thead>
    `;
}

/**
 * Cria uma linha <tr> da tabela para um item do planejamento.
 */
function criarLinhaItem(item) {
    const dataFormatada = new Date(item.data + 'T00:00:00').toLocaleDateString('pt-BR');
    const itemJsonString = JSON.stringify(item).replace(/'/g, "\\'");
    return `
        <tr>
            <td>${dataFormatada}</td>
            <td>${escapeHTML(item.semana || '')}</td>
            <td>${escapeHTML(item.horario || '')}</td>
            <td>${escapeHTML(item.cargaHoraria || '')}</td>
            <td>${escapeHTML(item.modalidade || '')}</td>
            <td>${escapeHTML(item.treinamento || '')}</td>
            <td>${escapeHTML(item.cmd || '')}</td>
            <td>${escapeHTML(item.sjb || '')}</td>
            <td>${escapeHTML(item.sagTombos || '')}</td>
            <td>${escapeHTML(item.instrutor || '')}</td>
            <td>${escapeHTML(item.local || '')}</td>
            <td>${escapeHTML(item.observacao || '')}</td>
            <td class="text-end">
                <button class="btn btn-sm btn-outline-primary" onclick='abrirModalParaEditar(${itemJsonString})'>
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="confirmarExclusao(${item.id})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `;
}

/**
 * Abre o modal de confirmação para excluir um item.
 */
window.confirmarExclusao = (id) => {
    itemParaExcluirId = id;
    confirmacaoModal.show();
};

/**
 * Executa a exclusão do item após a confirmação.
 */
async function executarExclusao() {
    if (!itemParaExcluirId) return;

    try {
        await chamarAPI(`/planejamento/itens/${itemParaExcluirId}`, 'DELETE');
        showToast('Item excluído com sucesso!', 'success');
        await carregarItens();
    } catch (error) {
        showToast(error.message, 'danger');
    } finally {
        itemParaExcluirId = null;
        confirmacaoModal.hide();
    }
}

