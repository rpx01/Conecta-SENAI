// Funções para administração de treinamentos e turmas

// Armazena os treinamentos do catálogo para uso no select do formulário
let treinamentosCatalogo = [];

/**
 * Carrega os treinamentos do catálogo e preenche o select de cadastro de turmas
 */
async function carregarTreinamentosSelect() {
    const select = document.getElementById('turmaTreinamentoId');
    if (!select) return; // Página não possui o select
    try {
        treinamentosCatalogo = await chamarAPI('/treinamentos/catalogo');
        // Limpa opções existentes
        select.innerHTML = '<option value="">Selecione...</option>';
        treinamentosCatalogo.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = t.nome;
            // Guarda se possui prática na opção para acesso rápido
            opt.dataset.temPratica = t.tem_pratica;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error('Erro ao carregar treinamentos:', e);
    }
}

/**
 * Mostra ou oculta o campo de data prática conforme o treinamento selecionado
 */
function atualizarCampoPratica() {
    const select = document.getElementById('turmaTreinamentoId');
    const grupo = document.getElementById('dataPraticaGroup');
    const input = document.getElementById('dataPratica');
    if (!select || !grupo || !input) return;
    const opt = select.options[select.selectedIndex];
    const temPratica = opt && opt.dataset.temPratica === 'true';
    if (temPratica) {
        grupo.classList.remove('d-none');
    } else {
        input.value = '';
        grupo.classList.add('d-none');
    }
}

async function carregarCatalogo() {
    try {
        const lista = await chamarAPI('/treinamentos/catalogo');
        const tbody = document.getElementById('catalogoTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        if (lista.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum treinamento cadastrado.</td></tr>';
            return;
        }
        for (const t of lista) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${t.id}</td>
                <td>${escapeHTML(t.nome)}</td>
                <td>${escapeHTML(t.codigo)}</td>
                <td>${t.carga_horaria || ''}</td>
                <td>${t.capacidade_maxima || ''}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editarTreinamento(${t.id})"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-outline-danger" onclick="excluirTreinamento(${t.id})"><i class="bi bi-trash"></i></button>
                </td>`;
            tbody.appendChild(tr);
        }
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

async function salvarTreinamento() {
    const id = document.getElementById('treinamentoId').value;
    const body = {
        nome: document.getElementById('nomeTrein').value,
        codigo: document.getElementById('codigoTrein').value,
        capacidade_maxima: parseInt(document.getElementById('capacidadeTrein').value) || null,
        carga_horaria: parseInt(document.getElementById('cargaTrein').value) || null,
        tem_pratica: document.getElementById('temPratica').checked,
        links_materiais: document.getElementById('linksTrein').value ? document.getElementById('linksTrein').value.split('\n') : null
    };
    try {
        if (id) {
            await chamarAPI(`/treinamentos/catalogo/${id}`, 'PUT', body);
        } else {
            await chamarAPI('/treinamentos/catalogo', 'POST', body);
        }
        bootstrap.Modal.getInstance(document.getElementById('treinamentoModal')).hide();
        carregarCatalogo();
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

function editarTreinamento(id) {
    chamarAPI(`/treinamentos/catalogo/${id}`).then(t => {
        document.getElementById('treinamentoId').value = t.id;
        document.getElementById('nomeTrein').value = t.nome;
        document.getElementById('codigoTrein').value = t.codigo;
        document.getElementById('capacidadeTrein').value = t.capacidade_maxima || '';
        document.getElementById('cargaTrein').value = t.carga_horaria || '';
        document.getElementById('temPratica').checked = t.tem_pratica;
        document.getElementById('linksTrein').value = (t.links_materiais || []).join('\n');
        new bootstrap.Modal(document.getElementById('treinamentoModal')).show();
    });
}

function limparFormularioTreinamento() {
    document.getElementById('treinamentoForm').reset();
    document.getElementById('treinamentoId').value = '';
}

function novoTreinamento() {
    limparFormularioTreinamento();
    new bootstrap.Modal(document.getElementById('treinamentoModal')).show();
}

async function excluirTreinamento(id) {
    if (!confirm('Excluir treinamento?')) return;
    try {
        await chamarAPI(`/treinamentos/catalogo/${id}`, 'DELETE');
        carregarCatalogo();
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

async function carregarTurmas() {
    try {
        const turmas = await chamarAPI('/treinamentos');
        const tbody = document.getElementById('turmasTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        if (turmas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhuma turma cadastrada.</td></tr>';
            return;
        }
        for (const t of turmas) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${t.turma_id}</td>
                <td>${escapeHTML(t.treinamento.nome)}</td>
                <td>${formatarData(t.data_inicio)}</td>
                <td>${formatarData(t.data_termino)}</td>
                <td>
                    <a class="btn btn-sm btn-outline-secondary me-1" href="/treinamentos/admin-inscricoes.html?turma=${t.turma_id}">Inscrições</a>
                    <button class="btn btn-sm btn-outline-primary" onclick="editarTurma(${t.turma_id})"><i class="bi bi-pencil"></i></button>
                </td>`;
            tbody.appendChild(tr);
        }
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

async function salvarTurma() {
    const id = document.getElementById('turmaId').value;
    const body = {
        treinamento_id: parseInt(document.getElementById('turmaTreinamentoId').value),
        data_inicio: document.getElementById('dataInicio').value,
        data_termino: document.getElementById('dataFim').value,
        data_treinamento_pratico: document.getElementById('dataPratica').value || null
    };
    try {
        if (id) {
            await chamarAPI(`/treinamentos/turmas/${id}`, 'PUT', body);
        } else {
            await chamarAPI('/treinamentos/turmas', 'POST', body);
        }
        bootstrap.Modal.getInstance(document.getElementById('turmaModal')).hide();
        carregarTurmas();
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

async function editarTurma(id) {
    const t = await chamarAPI(`/treinamentos/turmas/${id}`);
    await carregarTreinamentosSelect();
    document.getElementById('turmaId').value = t.id;
    document.getElementById('turmaTreinamentoId').value = t.treinamento_id;
    document.getElementById('dataInicio').value = t.data_inicio || '';
    document.getElementById('dataFim').value = t.data_termino || '';
    document.getElementById('dataPratica').value = t.data_treinamento_pratico || '';
    atualizarCampoPratica();
    new bootstrap.Modal(document.getElementById('turmaModal')).show();
}

function limparFormularioTurma() {
    document.getElementById('turmaForm').reset();
    document.getElementById('turmaId').value = '';
    atualizarCampoPratica();
}

function novaTurma() {
    limparFormularioTurma();
    carregarTreinamentosSelect();
    new bootstrap.Modal(document.getElementById('turmaModal')).show();
}

async function carregarInscricoes(turmaId) {
    try {
        const insc = await chamarAPI(`/treinamentos/turmas/${turmaId}/inscricoes`);
        const tbody = document.getElementById('inscricoesTableBody');
        tbody.innerHTML = '';
        if (insc.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhuma inscrição.</td></tr>';
            return;
        }
        for (const i of insc) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${i.id}</td>
                <td>${escapeHTML(i.nome)}</td>
                <td>${escapeHTML(i.email)}</td>
                <td>${i.cpf || ''}</td>
                <td>${escapeHTML(i.empresa || '')}</td>
            `;
            tbody.appendChild(tr);
        }
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

// Exporta a lista de inscrições da tabela para um arquivo XLSX
function exportarInscricoesXLSX() {
    const linhas = [
        ['ID', 'Nome', 'Email', 'CPF', 'Empresa'],
        ...Array.from(document.querySelectorAll('#inscricoesTableBody tr')).map(tr =>
            Array.from(tr.children).map(td => td.textContent.trim())
        )
    ];
    const ws = XLSX.utils.aoa_to_sheet(linhas);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Inscricoes');
    const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
    const blob = new Blob([wbout], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'inscricoes.xlsx';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
}

document.addEventListener('DOMContentLoaded', () => {
    verificarAutenticacao();
    verificarPermissaoAdmin();
    if (document.getElementById('catalogoTableBody')) carregarCatalogo();
    if (document.getElementById('turmasTableBody')) carregarTurmas();

    // Se existir o select de treinamentos, carrega opções e ajusta campo de prática
    if (document.getElementById('turmaTreinamentoId')) {
        carregarTreinamentosSelect().then(atualizarCampoPratica);
        document.getElementById('turmaTreinamentoId').addEventListener('change', atualizarCampoPratica);
    }

    const btnExportar = document.getElementById('btnExportarInscricoes');
    if (btnExportar) {
        btnExportar.addEventListener('click', exportarInscricoesXLSX);
    }
});

