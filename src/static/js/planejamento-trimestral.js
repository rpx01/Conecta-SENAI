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

    document.getElementById('itemDataInicio').addEventListener('change', calcularSemana);
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
        option.value = item.id;
        option.textContent = escapeHTML(item.nome ?? item.descricao ?? '');
        select.appendChild(option);
    });
}

/**
 * Converte uma data no formato brasileiro (dd/mm/yyyy) para ISO (yyyy-mm-dd).
 * @param {string} dataBr - Data no padrão brasileiro
 * @returns {string} Data no formato ISO
 */
function brToIsoDate(dataBr) {
    if (!dataBr) return '';
    const [dia, mes, ano] = dataBr.split('/');
    if (!dia || !mes || !ano) return '';
    return `${ano}-${mes.padStart(2, '0')}-${dia.padStart(2, '0')}`;
}

/**
 * Monta o payload esperado pela API de planejamento.
 * Realiza a validação dos campos obrigatórios.
 * @returns {object|null} Payload válido ou null se houver campos ausentes
 */
function montarPayloadPlanejamento() {
    const campos = {
        data_inicial: brToIsoDate(document.getElementById('itemDataInicio').value) || document.getElementById('itemDataInicio').value,
        data_final: brToIsoDate(document.getElementById('itemDataFim').value) || document.getElementById('itemDataFim').value,
        horario_id: Number(document.getElementById('itemHorario').value),
        carga_horaria_id: Number(document.getElementById('itemCargaHoraria').value),
        modalidade_id: Number(document.getElementById('itemModalidade').value),
        treinamento_id: Number(document.getElementById('itemTreinamento').value),
        instrutor_id: Number(document.getElementById('itemInstrutor').value),
        local_id: Number(document.getElementById('itemLocal').value),
        cmd_id: Number(document.getElementById('itemCmd').value),
        sjb_id: Number(document.getElementById('itemSjb').value),
        sag_tombos_id: Number(document.getElementById('itemSagTombos').value)
    };

    const nomesCampos = {
        data_inicial: 'Data Inicial',
        data_final: 'Data Final',
        horario_id: 'Horário',
        carga_horaria_id: 'Carga Horária',
        modalidade_id: 'Modalidade',
        treinamento_id: 'Treinamento',
        instrutor_id: 'Instrutor',
        local_id: 'Local',
        cmd_id: 'CMD',
        sjb_id: 'SJB',
        sag_tombos_id: 'SAG/TOMBOS'
    };

    const faltantes = Object.entries(campos)
        .filter(([chave, valor]) => {
            if (chave === 'data_inicial' || chave === 'data_final') {
                return !valor;
            }
            return Number.isNaN(valor);
        })
        .map(([chave]) => nomesCampos[chave]);

    if (faltantes.length) {
        showToast(`Preencha os campos: ${faltantes.join(', ')}`, 'warning');
        return null;
    }

    return campos;
}

/**
 * Calcula o número da semana com base na data selecionada.
 */
function calcularSemana() {
    const dataInput = document.getElementById('itemDataInicio').value;
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
window.abrirModalParaAdicionar = (loteId = '') => {
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
    document.getElementById('itemDataInicio').value = item.data;
    document.getElementById('itemDataFim').value = item.data;
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
 * Envia o planejamento para a API.
 */
async function salvarPlanejamento() {
    const payload = montarPayloadPlanejamento();
    if (!payload) return;

    try {
        const token = await obterCSRFToken();
        const resp = await fetch('/api/planejamentos', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': token
            },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) {
            let data = null;
            try { data = await resp.json(); } catch (_) {}
            const mensagem = data?.detail || (data?.errors && Object.values(data.errors).join(', ')) || 'Dados inválidos';
            showToast(mensagem, 'danger');
            return;
        }

        showToast('Item salvo com sucesso!', 'success');
        itemModal.hide();
        await carregarItens();
    } catch (error) {
        showToast('Dados inválidos', 'danger');
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
    const container = document.getElementById('planejamento-container');
    container.innerHTML = ''; // Limpa apenas o container específico

    const lotes = agruparItensPorLote(itens);

    if (Object.keys(lotes).length === 0) {
        container.innerHTML = `
            <div class="card">
                <div class="card-header bg-secondary text-white">
                    <h2 class="card-title mb-0">Planejamentos</h2>
                </div>
                <div class="card-body text-center">Nenhum item de planejamento encontrado.</div>
            </div>`;
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
        container.appendChild(loteCard);
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
