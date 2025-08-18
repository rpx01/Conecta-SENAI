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

/**
 * Função executada quando o DOM está totalmente carregado.
 */
document.addEventListener('DOMContentLoaded', async () => {
    itemModal = new bootstrap.Modal(document.getElementById('itemModal'));

    // Adiciona listener para calcular a semana quando a data muda
    document.getElementById('itemData').addEventListener('change', calcularSemana);

    // Inicia o carregamento dos dados da página
    await inicializarPagina();
});

/**
 * Orquestra o carregamento inicial dos dados da página.
 */
async function inicializarPagina() {
    try {
        // Carrega as opções dos selects e os itens do planejamento em paralelo
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
            // Informa o usuário sobre a falha, mas não impede o resto da página de carregar
            showToast(`Erro ao carregar dados para ${selectId.replace('item', '')}.`, 'warning');
        }
    });

    // Aguarda todas as buscas e preenchimentos terminarem
    await Promise.all(promessas);
}

/**
 * Popula um elemento <select> com os dados fornecidos.
 * @param {string} selectId - O ID do elemento <select>.
 * @param {Array} dados - Um array de objetos, cada um com 'id' e 'nome'.
 */
function popularSelect(selectId, dados) {
    const select = document.getElementById(selectId);
    if (!select) return;

    // Guarda a opção padrão "Selecione..."
    const placeholder = select.options[0];
    select.innerHTML = ''; // Limpa opções antigas
    select.appendChild(placeholder); // Adiciona a opção padrão de volta

    dados.forEach(item => {
        const option = document.createElement('option');
        // Usa o 'nome' como valor e texto, escapando para segurança
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
        const data = new Date(dataInput + "T00:00:00"); // Adiciona T00:00:00 para evitar problemas de fuso
        const primeiroDiaDoAno = new Date(data.getFullYear(), 0, 1);
        const diasPassados = Math.floor((data - primeiroDiaDoAno) / (24 * 60 * 60 * 1000));
        const semana = Math.ceil((data.getDay() + 1 + diasPassados) / 7);
        document.getElementById('itemSemana').value = `SEMANA ${semana}`;
    }
}

/**
 * Abre o modal para adicionar um novo item.
 * @param {string} loteId - O ID do lote (trimestre) onde o item será adicionado.
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
 * @param {object} item - O objeto com os dados do item a ser editado.
 */
window.abrirModalParaEditar = (item) => {
    document.getElementById('itemForm').reset();

    // Preenche os campos do formulário com os dados do item
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

    // Validação simples
    if (!dados.data || !dados.horario || !dados.treinamento) {
        showToast('Preencha todos os campos obrigatórios.', 'warning');
        return;
    }

    const endpoint = id ? `/planejamento/${id}` : '/planejamento';
    const method = id ? 'PUT' : 'POST';

    try {
        await chamarAPI(endpoint, method, dados);
        showToast(`Item ${id ? 'atualizado' : 'salvo'} com sucesso!`, 'success');
        itemModal.hide();
        carregarItens(); // Recarrega a lista
    } catch (error) {
        showToast(error.message, 'danger');
    }
}

/**
 * Carrega e renderiza todos os itens do planejamento.
 */
async function carregarItens() {
    // Esta função deve conter a sua lógica já existente para buscar e renderizar a tabela de planejamento.
    // Exemplo:
    try {
        const data = await chamarAPI('/planejamento');
        // Renderizar os lotes e itens...
    } catch (error) {
        showToast('Não foi possível carregar o planejamento.', 'danger');
    }
}

// Outras funções como renderizarLotes, excluirItem, etc. devem ser mantidas como estão.

