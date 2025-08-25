/* global bootstrap, chamarAPI, showToast, escapeHTML, executarAcaoComFeedback */

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
let edicaoId = null;
let edicaoLinhaId = null;
const itensCache = {};
const itensPorLote = {};
let planejamentoItens = [];
let originalData = [];
let sortDirection = {};

function formatarDataPtBr(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    const dd = String(d.getDate()).padStart(2, '0');
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const yyyy = d.getFullYear();
    return `${dd}/${mm}/${yyyy}`;
}

function getGroupKey(item) {
    if (item.grupo_id != null) return `g:${item.grupo_id}`;
    if (item.id_planejamento_grupo != null) return `g:${item.id_planejamento_grupo}`;
    if (item.loteId != null) return `g:${item.loteId}`;
    const nome = item.treinamento || item.nome_treinamento || item.nome || '';
    const dataFinal = item.data_final || '';
    const horario = item.horario || '';
    const modalidade = item.modalidade || '';
    const instrutor = item.instrutor_id || item.instrutor || '';
    const local = item.local || '';
    return [nome, dataFinal, horario, modalidade, instrutor, local].join('|');
}

function toDate(v) {
    return v ? new Date(v) : null;
}

function adicionarSufixoDias(lista) {
    const grupos = new Map();
    for (const it of lista) {
        const k = getGroupKey(it);
        if (!grupos.has(k)) grupos.set(k, []);
        grupos.get(k).push(it);
    }
    for (const arr of grupos.values()) {
        arr.sort((a, b) => toDate(a.data_inicial || a.data) - toDate(b.data_inicial || b.data));
        if (arr.length > 1) {
            arr.forEach((it, idx) => { it.__sufixoDia = ` - ${idx + 1}° dia`; });
        } else {
            arr[0].__sufixoDia = '';
        }
    }
}

function showDeleteConfirm(message) {
    return new Promise((resolve) => {
        const modalEl = document.getElementById('deleteConfirmModal');
        document.getElementById('deleteConfirmMessage').textContent = message;

        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        const btn = document.getElementById('deleteConfirmBtn');

        const onConfirm = () => { modal.hide(); cleanup(); resolve(true); };
        const onHidden = () => { cleanup(); resolve(false); };

        function cleanup() {
            btn.removeEventListener('click', onConfirm);
            modalEl.removeEventListener('hidden.bs.modal', onHidden);
        }

        btn.addEventListener('click', onConfirm);
        modalEl.addEventListener('hidden.bs.modal', onHidden);
        modal.show();
    });
}

function selecionarValor(selectEl, value) {
    if (value === undefined || value === null || value === '') return;
    selectEl.value = String(value);

    if (typeof $ !== 'undefined' && $(selectEl).trigger) {
        $(selectEl).trigger('change', { silent: true });
    }

    if (selectEl.value === '' || selectEl.value === 'undefined') {
        const opt = [...selectEl.options].find(o => o.textContent.trim() === String(value));
        if (opt) selectEl.value = opt.value;
    }
}

function toInputDate(yyyy_mm_dd) {
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(yyyy_mm_dd)) {
        const [d, m, y] = yyyy_mm_dd.split('/');
        return `${y}-${m}-${d}`;
    }
    return yyyy_mm_dd;
}

function toDisplayDate(yyyy_mm_dd) {
    const [y, m, d] = yyyy_mm_dd.split('-');
    return `${d}/${m}/${y}`;
}

function selecionarValorOuCriar(selectEl, valor, textoFallback) {
    if (valor == null || valor === '') {
        if (textoFallback) selecionarPorTexto(selectEl, textoFallback);
        return;
    }
    let opt = Array.from(selectEl.options).find(o => o.value == valor);
    if (!opt && textoFallback) {
        opt = new Option(textoFallback, valor, true, true);
        selectEl.add(opt);
    } else if (opt) {
        opt.selected = true;
    }
}

function selecionarPorTexto(selectEl, texto) {
    if (!texto) return;
    const opt = Array.from(selectEl.options).find(o => o.text.trim() === texto.trim());
    if (opt) opt.selected = true;
}

function preencherFormulario(item) {
    const form = document.getElementById('itemForm');
    form.reset();

    document.getElementById('itemId').value = item.id || '';
    document.getElementById('loteId').value = item.loteId || '';

    const dtIni = toInputDate(item.data_inicial || item.data);
    const dtFim = toInputDate(item.data_final || item.data);
    document.getElementById('itemDataInicio').value = dtIni;
    document.getElementById('itemDataFim').value = dtFim;
    document.getElementById('itemSemana').value = new Date(dtIni + 'T00:00:00').toLocaleDateString('pt-BR', { weekday: 'long' }).replace(/^./, c => c.toUpperCase());

    selecionarPorTexto(document.getElementById('itemHorario'), item.horario);
    selecionarPorTexto(document.getElementById('itemCargaHoraria'), item.cargaHoraria);
    selecionarPorTexto(document.getElementById('itemModalidade'), item.modalidade);
    selecionarPorTexto(document.getElementById('itemTreinamento'), item.treinamento);
    selecionarValorOuCriar(document.getElementById('itemCmd'), item.cmd_id, item.cmd);
    selecionarValorOuCriar(document.getElementById('itemSjb'), item.sjb_id, item.sjb);
    selecionarValorOuCriar(document.getElementById('itemSagTombos'), item.sag_tombos_id, item.sagTombos || item.sag_tombos);
    selecionarPorTexto(document.getElementById('itemInstrutor'), item.instrutor);
    selecionarPorTexto(document.getElementById('itemLocal'), item.local);

    document.getElementById('itemObservacao').value = item.observacao || '';
}

async function carregarCmd() {
    const dados = await chamarAPI('/planejamento-basedados/publico-alvo');
    popularSelect('itemCmd', dados);
}

async function carregarSjb() {
    const dados = await chamarAPI('/planejamento-basedados/publico-alvo');
    popularSelect('itemSjb', dados);
}

async function carregarSagTombos() {
    const dados = await chamarAPI('/planejamento-basedados/publico-alvo');
    popularSelect('itemSagTombos', dados);
}

async function obterItemPorId(idItem) {
    if (itensCache[idItem]) return itensCache[idItem];
    try {
        const item = await chamarAPI(`/planejamento/lote/${idItem}`);
        itensCache[idItem] = item;
        return item;
    } catch (error) {
        showToast('Falha ao obter item para edição', 'danger');
        throw error;
    }
}

/**
 * Função executada quando o DOM está totalmente carregado.
 */
document.addEventListener('DOMContentLoaded', async () => {
    itemModal = new bootstrap.Modal(document.getElementById('itemModal'));

    document.getElementById('itemDataInicio').addEventListener('change', calcularSemana);
    document.getElementById('btn-adicionar-planejamento').addEventListener('click', () => abrirModalParaAdicionar());
    document.getElementById('btnSalvarItem').addEventListener('click', salvarPlanejamento);
    document.getElementById('btnCancelarItem').addEventListener('click', () => { edicaoId = null; edicaoLinhaId = null; });
    document.getElementById('itemModal').addEventListener('hidden.bs.modal', () => { edicaoId = null; edicaoLinhaId = null; });

    const tabelaContainer = document.getElementById('planejamento-container');
    tabelaContainer.addEventListener('click', async (e) => {
        const btnEditar = e.target.closest('.btn-editar');
        if (btnEditar) {
            const idItem = btnEditar.dataset.itemId;
            const rowId = btnEditar.dataset.rowId;
            await abrirModalParaEditar(idItem, rowId);
            return;
        }

        const btnExcluir = e.target.closest('.btn-excluir');
        if (!btnExcluir) return;

        const idItem = btnExcluir.dataset.itemId;
        const titulo = btnExcluir.dataset.titulo || 'Treinamento';
        const dataIni = btnExcluir.dataset.dataInicialFormatada;
        const dataFim = btnExcluir.dataset.dataFinalFormatada;

        const ok = await showDeleteConfirm(
            `Confirma a exclusão?\n${titulo}\nPeríodo: ${dataIni} a ${dataFim}`
        );
        if (!ok) return;

        await executarAcaoComFeedback(btnExcluir, async () => {
            try {
                await chamarAPI(`/planejamento/lote/${idItem}`, 'DELETE');
                document.querySelectorAll(`[data-item-id="${idItem}"]`).forEach(tr => tr.remove());
                showToast('Item excluído com sucesso!', 'success');
            } catch (error) {
                showToast(error.message || 'Falha ao excluir item', 'danger');
                throw error;
            }
        });
    });

    const tableHeader = document.getElementById('table-header-planejamento');
    if (tableHeader) {
        tableHeader.addEventListener('click', (event) => {
            const th = event.target.closest('th');
            if (th && th.dataset.column) {
                sortTable(th.dataset.column);
            }
        });
    }

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
    const promessas = [carregarCmd(), carregarSjb(), carregarSagTombos()];

    const restante = { ...mapeamentoSelects };
    delete restante.itemCmd;
    delete restante.itemSjb;
    delete restante.itemSagTombos;

    Object.entries(restante).forEach(([selectId, endpoint]) => {
        promessas.push(
            chamarAPI(endpoint)
                .then(dados => popularSelect(selectId, dados))
                .catch(error => {
                    console.error(`Falha ao carregar opções para ${selectId}:`, error);
                    showToast(`Erro ao carregar dados para ${selectId.replace('item', '')}.`, 'warning');
                })
        );
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
        option.value = String(item.id);
        option.textContent = escapeHTML(item.nome ?? item.descricao ?? '');
        select.appendChild(option);
    });
}

async function montarRegistrosPlanejamento() {
    const dataInicio = document.getElementById('itemDataInicio').value;
    const dataFim = document.getElementById('itemDataFim').value;

    const selectsObrigatorios = ['itemHorario', 'itemCargaHoraria', 'itemModalidade', 'itemTreinamento', 'itemCmd', 'itemSjb', 'itemSagTombos', 'itemInstrutor', 'itemLocal'];
    const campos = { dataInicio, dataFim };
    selectsObrigatorios.forEach(id => { campos[id] = document.getElementById(id).value; });

    const nomesCampos = {
        dataInicio: 'Data Inicial',
        dataFim: 'Data Final',
        itemHorario: 'Horário',
        itemCargaHoraria: 'Carga Horária',
        itemModalidade: 'Modalidade',
        itemTreinamento: 'Treinamento',
        itemCmd: 'CMD',
        itemSjb: 'SJB',
        itemSagTombos: 'SAG/TOMBOS',
        itemInstrutor: 'Instrutor',
        itemLocal: 'Local'
    };

    const faltantes = Object.entries(campos)
        .filter(([_, valor]) => !valor)
        .map(([chave]) => nomesCampos[chave]);

    if (faltantes.length) {
        showToast(`Preencha os campos: ${faltantes.join(', ')}`, 'warning');
        return null;
    }

    const inicioDate = parseISODateToLocal(dataInicio);
    const fimDate = parseISODateToLocal(dataFim);
    if (fimDate < inicioDate) {
        showToast('Data final deve ser maior que a inicial', 'warning');
        return null;
    }

    const horario = document.getElementById('itemHorario').selectedOptions[0].textContent;
    const cargaHoraria = document.getElementById('itemCargaHoraria').selectedOptions[0].textContent;
    const modalidade = document.getElementById('itemModalidade').selectedOptions[0].textContent;
    const treinamento = document.getElementById('itemTreinamento').selectedOptions[0].textContent;
    const cmd = document.getElementById('itemCmd').selectedOptions[0].textContent;
    const sjb = document.getElementById('itemSjb').selectedOptions[0].textContent;
    const sagTombos = document.getElementById('itemSagTombos').selectedOptions[0].textContent;
    const instrutor = document.getElementById('itemInstrutor').selectedOptions[0].textContent;
    const local = document.getElementById('itemLocal').selectedOptions[0].textContent;
    const observacao = document.getElementById('itemObservacao').value;

    const loteIdInput = document.getElementById('loteId');
    const loteId = loteIdInput.value || crypto.randomUUID();
    loteIdInput.value = loteId;

    const registros = [];
    const feriadosSet = await loadCMDHolidaysBetween(inicioDate, fimDate);
    for (const d of eachBusinessDay(inicioDate, fimDate, feriadosSet)) {
        const iso = toISODateLocal(d);
        const diaSemana = d.toLocaleDateString('pt-BR', { weekday: 'long' });
        registros.push({
            data: iso,
            loteId,
            semana: diaSemana.charAt(0).toUpperCase() + diaSemana.slice(1),
            horario,
            carga_horaria: cargaHoraria,
            modalidade,
            treinamento,
            cmd,
            sjb,
            sag_tombos: sagTombos,
            instrutor,
            local,
            observacao
        });
    }

    return registros;
}

/**
 * Calcula o número da semana com base na data selecionada.
 */
function calcularSemana() {
    const dataInput = document.getElementById('itemDataInicio').value;
    if (dataInput) {
        const data = new Date(dataInput + 'T00:00:00');
        const diaSemana = data.toLocaleDateString('pt-BR', { weekday: 'long' });
        document.getElementById('itemSemana').value = diaSemana.charAt(0).toUpperCase() + diaSemana.slice(1);
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
    edicaoId = null;
    itemModal.show();
};

/**
 * Abre o modal para editar um item existente.
 */
window.abrirModalParaEditar = async (idItem, rowId) => {
    const item = await obterItemPorId(idItem);
    edicaoId = idItem;
    edicaoLinhaId = rowId;

    await Promise.all([carregarCmd(), carregarSjb(), carregarSagTombos()]);

    const lista = itensPorLote[idItem] || [];
    const linha = lista.find(it => String(it.id) === String(rowId));
    if (linha) {
        item.instrutor = linha.instrutor;
    }

    preencherFormulario(item);
    document.getElementById('itemId').value = rowId || '';

    document.getElementById('itemModalLabel').textContent = 'Editar Item do Planejamento';
    bootstrap.Modal.getOrCreateInstance(document.getElementById('itemModal')).show();
};


/**
 * Envia o planejamento para a API.
 */
async function salvarPlanejamento() {
    const registros = await montarRegistrosPlanejamento();
    if (!registros) return;
    const btnSalvar = document.getElementById('btnSalvarItem');
    try {
        await executarAcaoComFeedback(btnSalvar, async () => {
            if (edicaoId) {
                const itensOriginais = itensPorLote[edicaoId] || [];
                const promessas = itensOriginais.map((orig, idx) => {
                    const base = registros[idx] || registros[registros.length - 1];
                    const payload = { ...base };
                    if (String(orig.id) !== String(edicaoLinhaId)) {
                        payload.instrutor = orig.instrutor;
                    }
                    return chamarAPI(`/planejamento/itens/${orig.id}`, 'PUT', payload);
                });
                await Promise.all(promessas);
            } else {
                const promessas = registros.map(reg => chamarAPI('/planejamento/itens', 'POST', reg));
                await Promise.all(promessas);
            }
        });
        showToast('Item salvo com sucesso!', 'success');
        itemModal.hide();
        edicaoId = null;
        edicaoLinhaId = null;
        await carregarItens();
    } catch (error) {
        showToast(error.message || 'Dados inválidos', 'danger');
    }
}

/**
 * Carrega e renderiza todos os itens do planejamento.
 */
async function carregarItens() {
    try {
        const itens = await chamarAPI('/planejamento/itens');
        adicionarSufixoDias(itens);

        const dataFinalPorLote = {};
        itens.forEach(it => {
            const atual = dataFinalPorLote[it.loteId];
            dataFinalPorLote[it.loteId] = atual && atual > it.data ? atual : it.data;
            const d = new Date(it.data + 'T00:00:00');
            it.semana = d.toLocaleDateString('pt-BR', { weekday: 'long' });
        });
        itens.forEach(it => {
            it.data_final = dataFinalPorLote[it.loteId];
        });

        originalData = [...itens];
        planejamentoItens = [...itens];
        sortDirection = {};

        Object.keys(itensCache).forEach(k => delete itensCache[k]);
        Object.keys(itensPorLote).forEach(k => delete itensPorLote[k]);
        itens.forEach(it => {
            const id = it.loteId;
            if (!itensCache[id]) {
                itensCache[id] = { ...it, data_inicial: it.data, data_final: it.data };
            } else {
                if (it.data < itensCache[id].data_inicial) itensCache[id].data_inicial = it.data;
                if (it.data > itensCache[id].data_final) itensCache[id].data_final = it.data;
            }
            if (!itensPorLote[id]) itensPorLote[id] = [];
            itensPorLote[id].push(it);
        });

        renderizarItens(planejamentoItens);
    } catch (error) {
        showToast('Não foi possível carregar o planejamento.', 'danger');
    }
}

/**
 * Renderiza todos os itens do planejamento em uma única tabela.
 */
function renderizarItens(itens) {
    const tbody = document.getElementById('planejamento-tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (itens.length === 0) {
        tbody.innerHTML = '<tr><td colspan="16" class="text-center">Nenhum item de planejamento encontrado.</td></tr>';
        updateSortIcons();
        return;
    }

    itens.forEach(item => {
        tbody.insertAdjacentHTML('beforeend', criarLinhaItem(item));
    });

    updateSortIcons();
}

function sortTable(column) {
    if (!sortDirection[column]) {
        sortDirection = {};
        sortDirection[column] = 'asc';
    } else if (sortDirection[column] === 'asc') {
        sortDirection[column] = 'desc';
    } else {
        delete sortDirection[column];
        planejamentoItens = [...originalData];
        renderizarItens(planejamentoItens);
        return;
    }

    const sortedData = [...planejamentoItens];

    sortedData.sort((a, b) => {
        let valA = a[column];
        let valB = b[column];

        if (column === 'data' || column === 'data_final') {
            valA = new Date(valA);
            valB = new Date(valB);
        } else {
            if (typeof valA === 'string') valA = valA.toLowerCase();
            if (typeof valB === 'string') valB = valB.toLowerCase();
        }

        if (valA < valB) return sortDirection[column] === 'asc' ? -1 : 1;
        if (valA > valB) return sortDirection[column] === 'asc' ? 1 : -1;
        return 0;
    });

    planejamentoItens = sortedData;
    renderizarItens(sortedData);
}

function updateSortIcons() {
    const header = document.getElementById('table-header-planejamento');
    if (!header) return;

    header.querySelectorAll('th[data-column]').forEach(th => {
        const column = th.dataset.column;
        const baseText = th.textContent.replace(/[↕️🔼🔽]/g, '').trim();
        let icon = '↕️';
        if (sortDirection[column] === 'asc') icon = '🔼';
        else if (sortDirection[column] === 'desc') icon = '🔽';
        th.textContent = `${baseText} ${icon}`;
    });
}
/**
 * Cria uma linha <tr> da tabela para um item do planejamento.
 */
function criarLinhaItem(item) {
    const dataInicialFormatada = new Date(item.data + 'T00:00:00').toLocaleDateString('pt-BR');
    const dataFinalFormatada = new Date(item.data_final + 'T00:00:00').toLocaleDateString('pt-BR');
    const diaSemana = item.semana || '';
    return `
        <tr data-item-id="${item.loteId}">
            <td>${dataInicialFormatada}</td>
            <td>${dataFinalFormatada}</td>
            <td>${diaSemana.charAt(0).toUpperCase() + diaSemana.slice(1)}</td>
            <td>${escapeHTML(item.horario || '')}</td>
            <td>${escapeHTML(item.cargaHoraria || '')}</td>
            <td>${escapeHTML(item.modalidade || '')}</td>
            <td>${escapeHTML((item.treinamento || '') + (item.__sufixoDia || ''))}</td>
            <td>${escapeHTML(item.cmd || '')}</td>
            <td>${escapeHTML(item.sjb || '')}</td>
            <td>${escapeHTML(item.sagTombos || '')}</td>
            <td>${escapeHTML(item.instrutor || '')}</td>
            <td>${escapeHTML(item.local || '')}</td>
            <td>${escapeHTML(item.observacao || '')}</td>
            <td class="hidden-col" style="display: none;"></td>
            <td class="hidden-col" style="display: none;"></td>
            <td class="text-end">
                <button class="btn btn-sm btn-outline-primary btn-editar" data-item-id="${item.loteId}" data-row-id="${item.id}" data-data-inicial="${item.data}" data-data-final="${item.data_final}">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger btn-excluir" data-item-id="${item.loteId}" data-titulo="${escapeHTML(item.treinamento || '')}" data-data-inicial-formatada="${dataInicialFormatada}" data-data-final-formatada="${dataFinalFormatada}">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `;
}

/**
 * Renderiza uma linha de planejamento no DOM sem recriar toda a tabela.
 *
 * @param {Array} planejamento - Lista de itens do planejamento onde o
 *   último elemento é o item recentemente adicionado.
 */
function renderPlanejamento(planejamento) {
    const planejamentoList = document.getElementById('planejamento-list');
    let table = planejamentoList.querySelector('table');

    // Cria a estrutura da tabela caso ainda não exista
    if (!table) {
        table = document.createElement('table');
        table.className = 'table';
        planejamentoList.appendChild(table);

        const thead = document.createElement('thead');
        table.appendChild(thead);

        thead.innerHTML = `
            <tr>
                <th>Treinamento</th>
                <th>Carga Horária</th>
                <th>Tipo</th>
                <th>Categoria</th>
                <th>Data de Início</th>
                <th>Data de Término</th>
                <th>Ações</th>
            </tr>
        `;

        const tbody = document.createElement('tbody');
        tbody.id = 'planejamento-tbody';
        table.appendChild(tbody);
    }

    const tbody = document.getElementById('planejamento-tbody');

    // Caso a função seja usada para renderizar toda a lista, descomente a linha abaixo
    // tbody.innerHTML = '';

    const item = planejamento[planejamento.length - 1];
    const row = document.createElement('tr');
    row.dataset.id = item.id;
    row.innerHTML = `
        <td>${item.treinamento_nome}</td>
        <td>${item.carga_horaria}</td>
        <td>${item.tipo}</td>
        <td>${item.categoria}</td>
        <td>${new Date(item.data_inicio).toLocaleDateString()}</td>
        <td>${new Date(item.data_termino).toLocaleDateString()}</td>
        <td>
            <button class="btn btn-sm btn-info" onclick="editPlanejamento('${item.id}')">Editar</button>
            <button class="btn btn-sm btn-danger" onclick="deletePlanejamento('${item.id}')">Excluir</button>
        </td>
    `;
    tbody.appendChild(row);
}

document.addEventListener('change', (ev) => {
    const el = ev.target;
    if (el.classList.contains('sge-toggle')) {
        const row = el.closest('tr');
        const linkCell = row ? row.querySelector('td.link-col') : null;
        if (!linkCell) return;
        if (el.checked) {
            linkCell.innerHTML = `
                <input type="url" class="form-control form-control-sm sge-link-input" placeholder="https://...">
            `;
        } else {
            linkCell.innerHTML = '';
        }
        const payload = { sge_ativo: el.checked, sge_link: el.checked ? '' : null };
        chamarAPI(`/planejamento/itens/${el.dataset.id}`, 'PUT', payload)
            .catch(() => showToast('Não foi possível salvar o status SGE.', 'danger'));
    } else if (el.classList.contains('sge-link-input')) {
        const row = el.closest('tr');
        const toggle = row ? row.querySelector('.sge-toggle') : null;
        if (!toggle) return;
        const payload = { sge_ativo: true, sge_link: el.value.trim() };
        chamarAPI(`/planejamento/itens/${toggle.dataset.id}`, 'PUT', payload)
            .catch(() => showToast('Não foi possível salvar o link SGE.', 'danger'));
    }
});
