/* global chamarAPI, showToast, escapeHTML, parseISODateToLocal, loadCMDHolidaysBetween, isBusinessDay, toISODateLocal */

// Função para copiar o link de inscrição e dar feedback visual ao usuário
function copiarLink(event, link) {
    event.preventDefault();
    navigator.clipboard.writeText(link).then(() => {
        const button = event.target;
        button.textContent = 'Copiado!';
        button.classList.remove('btn-primary');
        button.classList.add('btn-success');
        setTimeout(() => {
            button.textContent = 'Copiar Link';
            button.classList.remove('btn-success');
            button.classList.add('btn-primary');
        }, 2000);
    }).catch(err => {
        console.error('Erro ao copiar o link: ', err);
        alert('Não foi possível copiar o link.');
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    await carregarItens();
});

/**
 * Carrega os itens de planejamento da API.
 */
async function carregarItens() {
    try {
        const agora = new Date();
        const inicio = new Date(agora.getFullYear(), 0, 1);
        const fim = new Date(agora.getFullYear() + 1, 11, 31);
        const feriadosSet = await loadCMDHolidaysBetween(inicio, fim);
        const itens = await chamarAPI('/planejamento/itens');
        renderizarItens(itens, feriadosSet);
    } catch (error) {
        // A função showToast é chamada para notificar o usuário em caso de erro.
        showToast('Não foi possível carregar o planejamento.', 'danger');
    }
}

/**
 * Renderiza os itens do planejamento na página.
 * @param {Array} itens - A lista de itens de planejamento.
 */
function renderizarItens(itens, feriadosSet) {
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
        </div>
    `;

    const tbody = document.getElementById('planejamento-tbody');
    tbody.innerHTML = '';

    if (!Array.isArray(itens) || itens.length === 0) {
        tbody.innerHTML = 'Nenhum item de planejamento encontrado.';
        return;
    }

    // Agrupa por loteId, guardando o item representativo (o de menor data) e o maior fim
    const grupos = new Map(); // loteId -> { primeiro, dataInicial, dataFinal }
    for (const it of itens) {
        const d = it.data;
        if (!grupos.has(it.loteId)) {
            grupos.set(it.loteId, { primeiro: it, dataInicial: d, dataFinal: d });
        } else {
            const g = grupos.get(it.loteId);
            if (d < g.dataInicial) {
                g.dataInicial = d;
                g.primeiro = it; // usar este item como referência para campos textuais
            }
            if (d > g.dataFinal) g.dataFinal = d;
        }
    }

    // Ordena por data inicial do lote (opcional, melhora leitura)
    const ordenados = [...grupos.values()].sort((a, b) =>
        String(a.dataInicial).localeCompare(String(b.dataInicial))
    );

    // 1 linha por lote: usar o item "primeiro" + dataFinal agregada
    for (const { primeiro, dataFinal } of ordenados) {
        tbody.insertAdjacentHTML('beforeend', criarLinhaItem(primeiro, dataFinal, feriadosSet));
    }
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
                <th>SGE</th>
                <th>LINK</th>
            </tr>
        </thead>
    `;
}

// Gera o botão de cópia do link de inscrição ou o campo de URL do SGE
function renderLinkCell(item) {
    if (!item.sge_ativo) {
        const url = `${window.location.origin}/inscricao_treinamento.html?treinamentoId=${encodeURIComponent(item.id)}&nome=${encodeURIComponent(item.treinamento)}`;
        return `<button class="btn btn-primary btn-sm" onclick="copiarLink(event, '${url}')">Copiar Link</button>`;
    }
    const value = item.sge_link || '';
    return `
        <input type="text" class="form-control form-control-sm sge-link-input"
               data-id="${item.id}" value="${escapeHTML(value)}" placeholder="https://..." />
    `;
}

/**
 * Cria uma linha da tabela para um item de planejamento.
 * @param {object} item - O item de planejamento.
 * @param {string} dataFinal - A data final do lote do item.
 * @returns {string} O HTML da linha da tabela.
 */
function criarLinhaItem(item, dataFinal, feriadosSet) {
    const dataObj = new Date(item.data + 'T00:00:00');
    const dataInicialFormatada = dataObj.toLocaleDateString('pt-BR');
    const dataFinalFormatada = new Date(dataFinal + 'T00:00:00').toLocaleDateString('pt-BR');
    const diaSemana = dataObj.toLocaleDateString('pt-BR', { weekday: 'long' });

    let limiteInscricaoHTML = '';
    if (item.treinamento !== 'NR 22 SEGURANCA E SAUDE OCUPACIONAL NA MINERACAO - AMBIENTACAO') {
        const inicio = parseISODateToLocal(item.data);
        const limite = new Date(inicio);
        let dias = 0;
        while (dias < 2) {
            limite.setDate(limite.getDate() - 1);
            if (isBusinessDay(limite, feriadosSet)) {
                dias++;
            }
        }
        const limiteFormatada = limite.toLocaleDateString('pt-BR');
        limiteInscricaoHTML = `O cadastro deve ser realizado até as 12H00 do dia ${limiteFormatada}`;
    }

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
            <td>${limiteInscricaoHTML}</td>
            <td>
                <label class="sge-switch" title="Ativar SGE">
                    <input type="checkbox" class="sge-toggle" data-id="${item.id || ''}" ${item.sge_ativo ? 'checked' : ''}>
                    <span class="sge-slider" aria-hidden="true"></span>
                </label>
            </td>
            <td class="link-col">${renderLinkCell(item)}</td>
        </tr>
    `;
}

document.addEventListener('change', async (ev) => {
    const el = ev.target;
    if (el.classList.contains('sge-toggle')) {
        if (!el.checked) {
            const confirmacao = confirm('Tem certeza que deseja desativar o SGE para este treinamento?');
            if (!confirmacao) {
                el.checked = true;
                return;
            }
        }

        const row = el.closest('tr');
        const linkCell = row ? row.querySelector('td.link-col') : null;
        if (!linkCell) return;

        const treinamentoNome = row ? row.querySelector('td:nth-child(7)')?.textContent.trim() : '';
        const itemAtualizado = {
            id: el.dataset.id,
            treinamento: treinamentoNome,
            sge_ativo: el.checked,
            sge_link: ''
        };
        linkCell.innerHTML = renderLinkCell(itemAtualizado);

        const payload = { sge_ativo: el.checked, sge_link: el.checked ? '' : null };
        try {
            await chamarAPI(`/planejamento/itens/${el.dataset.id}`, 'PUT', payload);
        } catch (e) {
            showToast('Não foi possível salvar o status SGE.', 'danger');
        }
    } else if (el.classList.contains('sge-link-input')) {
        const value = el.value.trim();
        if (value && !value.startsWith('http')) {
            showToast('Link inválido. Deve começar com http.', 'warning');
            return;
        }
        const row = el.closest('tr');
        const toggle = row ? row.querySelector('.sge-toggle') : null;
        if (!toggle) return;
        const payload = { sge_ativo: true, sge_link: value };
        chamarAPI(`/planejamento/itens/${toggle.dataset.id}`, 'PUT', payload)
            .catch(() => showToast('Não foi possível salvar o link SGE.', 'danger'));
    }
});

document.addEventListener('blur', (ev) => {
    const el = ev.target;
    if (el.classList.contains('sge-link-input')) {
        const value = el.value.trim();
        if (value && !value.startsWith('http')) {
            showToast('Link inválido. Deve começar com http.', 'warning');
        }
    }
}, true);

document.addEventListener('DOMContentLoaded', function () {
    const addItemModalEl = document.getElementById('addItemModal');
    if (addItemModalEl) {
        addItemModalEl.addEventListener('show.bs.modal', function () {
            loadUsers();
            loadTreinamentos();
        });
    }
});

