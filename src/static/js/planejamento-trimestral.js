/* global bootstrap, chamarAPI, showToast, escapeHTML, executarAcaoComFeedback */

const itensCache = {};
const itensPorLote = {};
window.itensPorLote = itensPorLote;

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
    document.getElementById('data-inicial').value = dtIni;
    document.getElementById('data-final').value = dtFim;
    document.getElementById('semana').value = new Date(dtIni + 'T00:00:00').toLocaleDateString('pt-BR', { weekday: 'long' }).replace(/^./, c => c.toUpperCase());

    selecionarPorTexto(document.getElementById('select-horario'), item.horario);
    selecionarPorTexto(document.getElementById('select-ch'), item.cargaHoraria);
    selecionarPorTexto(document.getElementById('select-modalidade'), item.modalidade);
    selecionarPorTexto(document.getElementById('select-treinamento'), item.treinamento);
    selecionarValorOuCriar(document.getElementById('select-cmd'), item.cmd_id, item.cmd);
    selecionarValorOuCriar(document.getElementById('select-sjb'), item.sjb_id, item.sjb);
    selecionarValorOuCriar(document.getElementById('select-sag_tombos'), item.sag_tombos_id, item.sagTombos || item.sag_tombos);
    selecionarPorTexto(document.getElementById('select-instrutor'), item.instrutor);
    selecionarPorTexto(document.getElementById('select-local'), item.local);

    document.getElementById('observacao').value = item.observacao || '';
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

window.abrirModalParaEditar = async (idItem, rowId) => {
    const item = await obterItemPorId(idItem);
    window.edicaoId = idItem;
    window.edicaoLinhaId = rowId;

    await Promise.all([carregarCmd(), carregarSjb(), carregarSagTombos()]);

    const lista = itensPorLote[idItem] || [];
    const linha = lista.find(it => String(it.id) === String(rowId));
    if (linha) {
        item.instrutor = linha.instrutor;
    }

    preencherFormulario(item);
    document.getElementById('itemId').value = rowId || '';

    document.getElementById('modalAdicionarPlanejamentoLabel').textContent = 'Editar Item do Planejamento';
    modalPlanejamento.show();
};

/**
 * Função executada quando o DOM está totalmente carregado.
 */
document.addEventListener('DOMContentLoaded', async () => {
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

    await carregarItens();
});

/**
 * Carrega e renderiza todos os itens do planejamento.
 */
async function carregarItens() {
    try {
        const itens = await chamarAPI('/planejamento/itens');
        adicionarSufixoDias(itens);

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

        renderizarItens(itens);
    } catch (error) {
        showToast('Não foi possível carregar o planejamento.', 'danger');
    }
}

/**
 * Renderiza todos os itens do planejamento em uma única tabela.
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
        tbody.innerHTML = '<tr><td colspan="14" class="text-center">Nenhum item de planejamento encontrado.</td></tr>';
        return;
    }

    // Calcula a data final para cada lote
    const dataFinalPorLote = {};
    itens.forEach(item => {
        const atual = dataFinalPorLote[item.loteId];
        dataFinalPorLote[item.loteId] = atual && atual > item.data ? atual : item.data;
    });

    itens.forEach(item => {
        const dataFinal = dataFinalPorLote[item.loteId];
        tbody.insertAdjacentHTML('beforeend', criarLinhaItem(item, dataFinal));
    });
}

/**
 * Cria o cabeçalho da tabela de itens.
 */
function criarCabecalhoTabela() {
    return `
        <thead>
            <tr>
                <th>Data Inicial</th><th>Data Final</th><th>Semana</th><th>Horário</th><th>C.H.</th>
                <th>Modalidade</th><th>Treinamento</th><th>CMD</th><th>SJB</th>
                <th>SAG/TOMBOS</th><th>Instrutor</th><th>Local</th><th>Obs.</th>
                <th class="hidden-col" style="display: none;">SGE</th><th class="hidden-col" style="display: none;">LINK</th>
                <th class="text-end">Ações</th>
            </tr>
        </thead>
    `;
}

/**
 * Cria uma linha <tr> da tabela para um item do planejamento.
 */
function criarLinhaItem(item, dataFinal) {
    const dataObj = new Date(item.data + 'T00:00:00');
    const dataInicialFormatada = dataObj.toLocaleDateString('pt-BR');
    const dataFinalFormatada = new Date(dataFinal + 'T00:00:00').toLocaleDateString('pt-BR');
    const diaSemana = dataObj.toLocaleDateString('pt-BR', { weekday: 'long' });
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
            <!--
            <td>
                <label class="sge-switch" title="Ativar SGE">
                    <input type="checkbox" class="sge-toggle" data-id="${item.id || ''}" ${item.sge_ativo ? 'checked' : ''}>
                    <span class="sge-slider" aria-hidden="true"></span>
                </label>
            </td>
            <td class="link-col">${item.sge_ativo ? `<input type='url' class='form-control form-control-sm sge-link-input' placeholder='https://...' value='${escapeHTML(item.sge_link || '')}'>` : ''}</td>
            -->
            <td class="text-end">
                <button class="btn btn-sm btn-outline-primary btn-editar" data-item-id="${item.loteId}" data-row-id="${item.id}" data-data-inicial="${item.data}" data-data-final="${dataFinal}">
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
