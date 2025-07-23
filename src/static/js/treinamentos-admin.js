// Funções para administração de treinamentos e turmas

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
        tipo: document.getElementById('tipoTrein').value,
        conteudo_programatico: document.getElementById('conteudoTrein').value,
        carga_horaria: parseInt(document.getElementById('cargaTrein').value) || null,
        capacidade_maxima: parseInt(document.getElementById('capacidadeTrein').value) || null,
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

async function editarTreinamento(id) {
    try {
        const t = await chamarAPI(`/treinamentos/catalogo/${id}`);
        document.getElementById('treinamentoId').value = t.id;
        document.getElementById('nomeTrein').value = t.nome;
        document.getElementById('codigoTrein').value = t.codigo;
        document.getElementById('tipoTrein').value = t.tipo || 'Inicial';
        document.getElementById('conteudoTrein').value = t.conteudo_programatico || '';
        document.getElementById('cargaTrein').value = t.carga_horaria || '';
        document.getElementById('capacidadeTrein').value = t.capacidade_maxima || '';
        document.getElementById('temPratica').checked = t.tem_pratica;
        document.getElementById('linksTrein').value = (t.links_materiais || []).join('\n');
        new bootstrap.Modal(document.getElementById('treinamentoModal')).show();
    } catch(e) {
        exibirAlerta(`Erro ao carregar dados para edição: ${e.message}`, 'danger');
    }
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
                <td>${formatarData(t.data_fim)}</td>
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
        data_fim: document.getElementById('dataFim').value,
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
    try {
        const t = await chamarAPI(`/api/treinamentos/turmas/${id}`);
        document.getElementById('turmaId').value = t.id;
        document.getElementById('turmaTreinamentoId').value = t.treinamento_id;
        document.getElementById('dataInicio').value = t.data_inicio ? t.data_inicio.split('T')[0] : '';
        document.getElementById('dataFim').value = t.data_fim ? t.data_fim.split('T')[0] : '';
        document.getElementById('dataPratica').value = t.data_treinamento_pratico ? t.data_treinamento_pratico.split('T')[0] : '';
        new bootstrap.Modal(document.getElementById('turmaModal')).show();
    } catch(e) {
        exibirAlerta(`Erro ao carregar dados da turma: ${e.message}`, 'danger');
    }
}

async function carregarInscricoes(turmaId) {
    try {
        const insc = await chamarAPI(`/treinamentos/turmas/${turmaId}/inscricoes`);
        const tbody = document.getElementById('inscricoesTableBody');
        tbody.innerHTML = '';
        if (insc.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhuma inscrição.</td></tr>';
            return;
        }
        for (const i of insc) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${i.id}</td>
                <td>${escapeHTML(i.nome)}</td>
                <td>${escapeHTML(i.email)}</td>
                <td>${i.cpf || ''}</td>
            `;
            tbody.appendChild(tr);
        }
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    verificarAutenticacao();
    verificarPermissaoAdmin();
    if (document.getElementById('catalogoTableBody')) carregarCatalogo();
    if (document.getElementById('turmasTableBody')) carregarTurmas();
});
