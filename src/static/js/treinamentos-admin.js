// Funções para administração de treinamentos e turmas

// Armazena a lista de treinamentos para não ter que recarregar toda vez
let catalogoDeTreinamentos = [];

// Função para limpar e abrir o modal de Treinamento (Catálogo)
function novoTreinamento() {
    document.getElementById('treinamentoForm').reset();
    document.getElementById('treinamentoId').value = '';
    document.getElementById('tipoTrein').value = 'Inicial';
    new bootstrap.Modal(document.getElementById('treinamentoModal')).show();
}

// Carrega o catálogo de treinamentos na tabela
async function carregarCatalogo() {
    try {
        const lista = await chamarAPI('/treinamentos/catalogo');
        catalogoDeTreinamentos = lista; // Armazena para uso no modal de turmas
        const tbody = document.getElementById('catalogoTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        if (lista.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">Nenhum treinamento cadastrado.</td></tr>';
            return;
        }
        for (const t of lista) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${t.id}</td>
                <td>${escapeHTML(t.nome)}</td>
                <td>${escapeHTML(t.codigo)}</td>
                <td>${escapeHTML(t.tipo || '')}</td>
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

// Salva um treinamento (novo ou existente)
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
        const endpoint = id ? `/treinamentos/catalogo/${id}` : '/treinamentos/catalogo';
        const method = id ? 'PUT' : 'POST';
        await chamarAPI(endpoint, method, body);
        bootstrap.Modal.getInstance(document.getElementById('treinamentoModal')).hide();
        carregarCatalogo();
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

// Preenche o modal de treinamento para edição
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

// Exclui um treinamento do catálogo
async function excluirTreinamento(id) {
    if (!confirm('Excluir treinamento?')) return;
    try {
        await chamarAPI(`/treinamentos/catalogo/${id}`, 'DELETE');
        carregarCatalogo();
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

// Carrega a lista de turmas na tabela
async function carregarTurmas() {
    try {
        const turmas = await chamarAPI('/treinamentos');
        const tbody = document.getElementById('turmasTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        if (turmas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhuma turma cadastrada.</td></tr>';
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
                    <a class="btn btn-sm btn-outline-info me-1" href="/treinamentos/admin-inscricoes.html?turma=${t.turma_id}" title="Ver Inscrições"><i class="bi bi-people"></i></a>
                    <button class="btn btn-sm btn-outline-primary" onclick="editarTurma(${t.turma_id})" title="Editar Turma"><i class="bi bi-pencil"></i></button>
                </td>`;
            tbody.appendChild(tr);
        }
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

/**
 * Função centralizada para abrir o modal de turma, seja para criar ou editar.
 * @param {number|null} id - O ID da turma para editar, ou null para criar uma nova.
 */
async function abrirModalTurma(id = null) {
    const form = document.getElementById('turmaForm');
    form.reset();
    document.getElementById('turmaId').value = id || '';

    // Popula o select de treinamentos
    const select = document.getElementById('turmaTreinamentoId');
    select.innerHTML = '<option value="">Selecione um treinamento...</option>';
    if (catalogoDeTreinamentos.length === 0) {
        await carregarCatalogo(); // Garante que o catálogo está carregado
    }
    catalogoDeTreinamentos.forEach(t => {
        select.innerHTML += `<option value="${t.id}">${escapeHTML(t.nome)}</option>`;
    });

    // Se for edição, busca os dados da turma
    if (id) {
        try {
            const t = await chamarAPI(`/treinamentos/turmas/${id}`);
            select.value = t.treinamento_id;
            document.getElementById('dataInicio').value = t.data_inicio ? t.data_inicio.split('T')[0] : '';
            document.getElementById('dataFim').value = t.data_fim ? t.data_fim.split('T')[0] : '';
            
            // Dispara o evento de change para atualizar a visibilidade do campo de data prática
            select.dispatchEvent(new Event('change'));
            
            document.getElementById('dataPratica').value = t.data_treinamento_pratico ? t.data_treinamento_pratico.split('T')[0] : '';
        } catch(e) {
            exibirAlerta(`Erro ao carregar dados da turma: ${e.message}`, 'danger');
            return; // Não abre o modal se houver erro
        }
    } else {
        // Se for novo, apenas limpa o campo de data prática e garante que está oculto
        document.getElementById('dataPraticaGroup').classList.add('d-none');
        document.getElementById('dataPratica').value = '';
    }

    new bootstrap.Modal(document.getElementById('turmaModal')).show();
}

// (NOVA FUNÇÃO) - Chamada pelo botão "NOVA TURMA"
function novaTurma() {
    abrirModalTurma(null);
}

// (FUNÇÃO CORRIGIDA) - Chamada pelo botão de editar
function editarTurma(id) {
    abrirModalTurma(id);
}

// Salva a turma (nova ou existente)
async function salvarTurma() {
    const id = document.getElementById('turmaId').value;
    const body = {
        treinamento_id: parseInt(document.getElementById('turmaTreinamentoId').value),
        data_inicio: document.getElementById('dataInicio').value,
        data_fim: document.getElementById('dataFim').value,
        data_treinamento_pratico: document.getElementById('dataPratica').value || null
    };

    if (!body.treinamento_id || !body.data_inicio || !body.data_fim) {
        exibirAlerta("Por favor, preencha todos os campos obrigatórios.", "warning");
        return;
    }

    try {
        const endpoint = id ? `/treinamentos/turmas/${id}` : '/treinamentos/turmas';
        const method = id ? 'PUT' : 'POST';
        await chamarAPI(endpoint, method, body);
        bootstrap.Modal.getInstance(document.getElementById('turmaModal')).hide();
        carregarTurmas();
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

// Carrega as inscrições de uma turma específica
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
                <td>${i.empresa || ''}</td>
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
    if (document.getElementById('catalogoTableBody')) {
        carregarCatalogo();
    }
    if (document.getElementById('turmasTableBody')) {
        carregarTurmas();
    }

    const formTreinamento = document.getElementById('treinamentoForm');
    if (formTreinamento) {
        formTreinamento.addEventListener('submit', (e) => {
            e.preventDefault();
            salvarTreinamento();
        });
    }

    // Listener para o select de treinamento no modal de turma
    const selectTreinamento = document.getElementById('turmaTreinamentoId');
    if (selectTreinamento) {
        selectTreinamento.addEventListener('change', () => {
            const dataPraticaGroup = document.getElementById('dataPraticaGroup');
            const selectedId = parseInt(selectTreinamento.value);
            const treinamento = catalogoDeTreinamentos.find(t => t.id === selectedId);

            if (treinamento && treinamento.tem_pratica) {
                dataPraticaGroup.classList.remove('d-none');
            } else {
                dataPraticaGroup.classList.add('d-none');
                document.getElementById('dataPratica').value = ''; // Limpa o campo se não tiver prática
            }
        });
    }
});
