/* global chamarAPI, showToast, escapeHTML, parseISODateToLocal, loadCMDHolidaysBetween, eachBusinessDay, toISODateLocal, executarAcaoComFeedback, bootstrap */

const selectEndpoints = {
    'select-horario': '/planejamento-basedados/horario',
    'select-ch': '/planejamento-basedados/cargahoraria',
    'select-modalidade': '/planejamento-basedados/modalidade',
    'select-treinamento': '/planejamento-basedados/treinamento',
    'select-cmd': '/planejamento-basedados/publico-alvo',
    'select-sjb': '/planejamento-basedados/publico-alvo',
    'select-sag_tombos': '/planejamento-basedados/publico-alvo',
    'select-instrutor': '/instrutores',
    'select-local': '/planejamento-basedados/local'
};

function popularSelect(selectEl, dados) {
    if (!selectEl) return;
    const placeholder = selectEl.options[0];
    selectEl.innerHTML = '';
    if (placeholder) selectEl.appendChild(placeholder);
    dados.forEach(item => {
        const option = document.createElement('option');
        option.value = String(item.id);
        option.textContent = escapeHTML(item.nome ?? item.descricao ?? '');
        selectEl.appendChild(option);
    });
}

async function carregarCmd() {
    const dados = await chamarAPI('/planejamento-basedados/publico-alvo');
    popularSelect(document.getElementById('select-cmd'), dados);
}

async function carregarSjb() {
    const dados = await chamarAPI('/planejamento-basedados/publico-alvo');
    popularSelect(document.getElementById('select-sjb'), dados);
}

async function carregarSagTombos() {
    const dados = await chamarAPI('/planejamento-basedados/publico-alvo');
    popularSelect(document.getElementById('select-sag_tombos'), dados);
}

async function carregarOpcoesDosSelects() {
    const promessas = [carregarCmd(), carregarSjb(), carregarSagTombos()];
    const restante = { ...selectEndpoints };
    delete restante['select-cmd'];
    delete restante['select-sjb'];
    delete restante['select-sag_tombos'];

    Object.entries(restante).forEach(([id, endpoint]) => {
        promessas.push(
            chamarAPI(endpoint)
                .then(dados => popularSelect(document.getElementById(id), dados))
                .catch(error => {
                    console.error(`Falha ao carregar opções para ${id}:`, error);
                    showToast(`Erro ao carregar dados para ${id.replace('select-', '')}.`, 'warning');
                })
        );
    });

    await Promise.all(promessas);
}

function calcularSemana() {
    const dataInput = document.getElementById('data-inicial').value;
    if (dataInput) {
        const data = new Date(dataInput + 'T00:00:00');
        const diaSemana = data.toLocaleDateString('pt-BR', { weekday: 'long' });
        document.getElementById('semana').value = diaSemana.charAt(0).toUpperCase() + diaSemana.slice(1);
    }
}

async function montarRegistrosPlanejamento() {
    const dataInicio = document.getElementById('data-inicial').value;
    const dataFim = document.getElementById('data-final').value;

    const selectsObrigatorios = ['select-horario', 'select-ch', 'select-modalidade', 'select-treinamento', 'select-cmd', 'select-sjb', 'select-sag_tombos', 'select-instrutor', 'select-local'];
    const campos = { dataInicio, dataFim };
    selectsObrigatorios.forEach(id => { campos[id] = document.getElementById(id).value; });

    const nomesCampos = {
        dataInicio: 'Data Inicial',
        dataFim: 'Data Final',
        'select-horario': 'Horário',
        'select-ch': 'C.H. (Carga Horária)',
        'select-modalidade': 'Modalidade',
        'select-treinamento': 'Treinamento',
        'select-cmd': 'CMD',
        'select-sjb': 'SJB',
        'select-sag_tombos': 'SAG/TOMBOS',
        'select-instrutor': 'Instrutor',
        'select-local': 'Local'
    };

    const faltantes = Object.entries(campos)
        .filter(([, valor]) => !valor)
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

    const horario = document.getElementById('select-horario').selectedOptions[0].textContent;
    const cargaHoraria = document.getElementById('select-ch').selectedOptions[0].textContent;
    const modalidade = document.getElementById('select-modalidade').selectedOptions[0].textContent;
    const treinamento = document.getElementById('select-treinamento').selectedOptions[0].textContent;
    const cmd = document.getElementById('select-cmd').selectedOptions[0].textContent;
    const sjb = document.getElementById('select-sjb').selectedOptions[0].textContent;
    const sagTombos = document.getElementById('select-sag_tombos').selectedOptions[0].textContent;
    const instrutor = document.getElementById('select-instrutor').selectedOptions[0].textContent;
    const local = document.getElementById('select-local').selectedOptions[0].textContent;
    const observacao = document.getElementById('observacao').value;

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

async function salvarPlanejamento() {
    const registros = await montarRegistrosPlanejamento();
    if (!registros) return;
    const btnSalvar = document.getElementById('btnSalvarItem');
    try {
        await executarAcaoComFeedback(btnSalvar, async () => {
            if (window.edicaoId) {
                const itensOriginais = (window.itensPorLote || {})[window.edicaoId] || [];
                const promessas = itensOriginais.map((orig, idx) => {
                    const base = registros[idx] || registros[registros.length - 1];
                    const payload = { ...base };
                    if (String(orig.id) !== String(window.edicaoLinhaId)) {
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
        modalPlanejamento.hide();
        window.edicaoId = null;
        window.edicaoLinhaId = null;
        if (typeof window.carregarItens === 'function') {
            await window.carregarItens();
        }
    } catch (error) {
        showToast(error.message || 'Dados inválidos', 'danger');
    }
}

window.abrirModalParaAdicionar = function(loteId = '') {
    const form = document.getElementById('itemForm');
    form.reset();
    document.getElementById('itemId').value = '';
    document.getElementById('loteId').value = loteId;
    document.getElementById('modalAdicionarPlanejamentoLabel').textContent = 'Adicionar Item ao Planejamento';
    window.edicaoId = null;
    window.edicaoLinhaId = null;
};

let modalPlanejamento;

window.initModalPlanejamento = async function initModalPlanejamento() {
    window.edicaoId = null;
    window.edicaoLinhaId = null;
    window.itensPorLote = window.itensPorLote || {};
    modalPlanejamento = new bootstrap.Modal(document.getElementById('modalAdicionarPlanejamento'));
    window.modalPlanejamento = modalPlanejamento;

    await carregarOpcoesDosSelects();

    document.getElementById('data-inicial').addEventListener('change', calcularSemana);
    document.getElementById('btnSalvarItem').addEventListener('click', salvarPlanejamento);
    document.getElementById('btnCancelarItem').addEventListener('click', () => {
        window.edicaoId = null;
        window.edicaoLinhaId = null;
    });
    document.getElementById('modalAdicionarPlanejamento').addEventListener('hidden.bs.modal', () => {
        window.edicaoId = null;
        window.edicaoLinhaId = null;
    });

    const btnAdd = document.getElementById('btn-adicionar-planejamento');
    if (btnAdd) {
        btnAdd.addEventListener('click', () => abrirModalParaAdicionar());
    }
};
