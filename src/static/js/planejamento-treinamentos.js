/* global chamarAPI, showToast, escapeHTML */

document.addEventListener('DOMContentLoaded', async () => {
    await carregarItens();
});

/**
 * Carrega os itens de planejamento da API.
 */
async function carregarItens() {
    try {
        const itens = await chamarAPI('/planejamento/itens');
        renderizarItens(itens);
    } catch (error) {
        // A função showToast é chamada para notificar o usuário em caso de erro.
        showToast('Não foi possível carregar o planejamento.', 'danger');
    }
}

/**
 * Renderiza os itens do planejamento na página.
 * @param {Array} itens - A lista de itens de planejamento.
 */
function renderizarItens(itens) {
    const container = document.getElementById('planejamento-container');

    container.innerHTML = `
        <div class="card mb-4">
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table id="tabela-planejamento" class="table table-striped table-hover mb-0">
                        ${criarCabecalhoTabela()}
                        <tbody id="planejamento-tbody"></tbody>
                    </table>
                </div>
            </div>
        </div>`;

    const tbody = document.getElementById('planejamento-tbody');
    tbody.innerHTML = '';

    if (itens.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center">Nenhum item de planejamento encontrado.</td></tr>';
        return;
    }

    // Agrupa os itens por lote para encontrar a data final correta de cada treinamento.
    const dataFinalPorLote = {};
    itens.forEach(item => {
        const atual = dataFinalPorLote[item.loteId];
        dataFinalPorLote[item.loteId] = (atual && atual > item.data) ? atual : item.data;
    });

    itens.forEach(item => {
        const dataFinal = dataFinalPorLote[item.loteId];
        tbody.insertAdjacentHTML('beforeend', criarLinhaItem(item, dataFinal));
    });
}

/**
 * Cria o cabeçalho da tabela.
 * @returns {string} O HTML do cabeçalho da tabela.
 */
function criarCabecalhoTabela() {
    return `
        <thead>
            <tr>
                <th>DATA INICIO</th>
                <th>DATA TERMINO</th>
                <th>SEMANA</th>
                <th>HORÁRIO</th>
                <th>CARGA HORÁRIA</th>
                <th>MODALIDADE</th>
                <th>TREINAMENTO</th>
                <th>LOCAL</th>
                <th>LIMITE DE INSCRIÇÃO</th>
                <th>LINK</th>
            </tr>
        </thead>
    `;
}

/**
 * Cria uma linha da tabela para um item de planejamento.
 * @param {object} item - O item de planejamento.
 * @param {string} dataFinal - A data final do lote do item.
 * @returns {string} O HTML da linha da tabela.
 */
function criarLinhaItem(item, dataFinal) {
    const dataObj = new Date(item.data + 'T00:00:00');
    const dataInicialFormatada = dataObj.toLocaleDateString('pt-BR');
    const dataFinalFormatada = new Date(dataFinal + 'T00:00:00').toLocaleDateString('pt-BR');
    const diaSemana = dataObj.toLocaleDateString('pt-BR', { weekday: 'long' });

    // As colunas 'LIMITE DE INSCRIÇÃO' e 'LINK' são deixadas em branco
    // pois não há dados correspondentes no objeto 'item'.
    return `
        <tr>
            <td>${dataInicialFormatada}</td>
            <td>${dataFinalFormatada}</td>
            <td>${diaSemana.charAt(0).toUpperCase() + diaSemana.slice(1)}</td>
            <td>${escapeHTML(item.horario || '')}</td>
            <td>${escapeHTML(item.cargaHoraria || '')}</td>
            <td>${escapeHTML(item.modalidade || '')}</td>
            <td>${escapeHTML(item.treinamento || '')}</td>
            <td>${escapeHTML(item.local || '')}</td>
            <td></td>
            <td></td>
        </tr>
    `;
}

