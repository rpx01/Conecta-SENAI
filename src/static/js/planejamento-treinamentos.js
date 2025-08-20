/* global chamarAPI, showToast, escapeHTML, parseISODateToLocal, loadCMDHolidaysBetween, isBusinessDay, toISODateLocal */

document.addEventListener('DOMContentLoaded', async () => {
    await carregarItens();
});

const API_BASE = '/planejamentos-treinamentos';

async function carregarItens() {
    try {
        const agora = new Date();
        const inicio = new Date(agora.getFullYear(), 0, 1);
        const fim = new Date(agora.getFullYear() + 1, 11, 31);
        const feriadosSet = await loadCMDHolidaysBetween(inicio, fim);
        const itens = await chamarAPI('/planejamento/itens');
        renderizarItens(itens, feriadosSet);
    } catch (error) {
        showToast('Não foi possível carregar o planejamento.', 'danger');
    }
}

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

    const grupos = new Map();
    for (const it of itens) {
        const d = it.data;
        if (!grupos.has(it.loteId)) {
            grupos.set(it.loteId, { primeiro: it, dataInicial: d, dataFinal: d });
        } else {
            const g = grupos.get(it.loteId);
            if (d < g.dataInicial) {
                g.dataInicial = d;
                g.primeiro = it;
            }
            if (d > g.dataFinal) g.dataFinal = d;
        }
    }

    const ordenados = [...grupos.values()].sort((a, b) =>
        String(a.dataInicial).localeCompare(String(b.dataInicial))
    );

    for (const { primeiro, dataFinal } of ordenados) {
        tbody.insertAdjacentHTML('beforeend', criarLinhaItem(primeiro, dataFinal, feriadosSet));
        const tr = tbody.lastElementChild;
        hydrateSgeUi(tr, primeiro);
    }
}

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
                    <input type="checkbox" data-role="sge-toggle">
                    <span class="sge-slider" aria-hidden="true"></span>
                </label>
            </td>
            <td><input type="url" class="form-control form-control-sm" data-role="sge-link" placeholder="https://..."></td>
        </tr>
    `;
}

function saveSGE(id, sgeAtivo, sgeLink) {
    return chamarAPI(`${API_BASE}/${id}/sge`, 'PATCH', {
        sge_ativo: !!sgeAtivo,
        sge_link: sgeAtivo ? (sgeLink && sgeLink.trim() ? sgeLink.trim() : null) : null
    });
}

function onToggleChange(ev) {
    const toggle = ev.currentTarget;
    const id = toggle.dataset.id;
    const checked = toggle.checked;
    const row = toggle.closest('tr');
    const linkInput = row.querySelector(`input[data-role="sge-link"][data-id="${id}"]`);

    if (checked) {
        linkInput.removeAttribute('disabled');
        linkInput.parentElement.style.display = '';
    } else {
        linkInput.value = '';
        linkInput.setAttribute('disabled', 'disabled');
        linkInput.parentElement.style.display = 'none';
    }

    saveSGE(id, checked, linkInput.value).catch(err => {
        toggle.checked = !checked;
        if (!toggle.checked) {
            linkInput.value = '';
            linkInput.setAttribute('disabled', 'disabled');
            linkInput.parentElement.style.display = 'none';
        }
        console.error(err);
        alert('Não foi possível salvar SGE/LINK.');
    });
}

function onLinkCommit(ev) {
    const input = ev.currentTarget;
    const id = input.dataset.id;
    const row = input.closest('tr');
    const toggle = row.querySelector(`input[type="checkbox"][data-role="sge-toggle"][data-id="${id}"]`);
    saveSGE(id, toggle.checked, input.value).catch(err => {
        console.error(err);
        alert('Não foi possível salvar o LINK.');
    });
}

function onKeyDownCommit(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        e.currentTarget.blur();
    }
}

function hydrateSgeUi(rowElement, item) {
    const toggle = rowElement.querySelector('input[type="checkbox"][data-role="sge-toggle"]');
    const input = rowElement.querySelector('input[data-role="sge-link"]');

    toggle.dataset.id = item.id;
    input.dataset.id = item.id;

    toggle.checked = !!item.sge_ativo;
    input.value = item.sge_link || '';

    if (toggle.checked) {
        input.removeAttribute('disabled');
        input.parentElement.style.display = '';
    } else {
        input.setAttribute('disabled', 'disabled');
        input.parentElement.style.display = 'none';
    }

    toggle.removeEventListener('change', onToggleChange);
    toggle.addEventListener('change', onToggleChange);

    input.removeEventListener('blur', onLinkCommit);
    input.addEventListener('blur', onLinkCommit);

    input.removeEventListener('keydown', onKeyDownCommit);
    input.addEventListener('keydown', onKeyDownCommit);
}
