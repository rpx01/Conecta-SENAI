// Funções para administração de treinamentos e turmas

// Armazena a lista de treinamentos e instrutores para não ter que recarregar
let catalogoDeTreinamentos = [];
let listaDeInstrutores = [];

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

// Carrega instrutores para o select
async function carregarInstrutores() {
    if (listaDeInstrutores.length > 0) return; // Evita recarregar
    try {
        listaDeInstrutores = await chamarAPI('/instrutores');
    } catch(e) {
        console.error("Falha ao carregar instrutores", e);
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
    const selectTrein = document.getElementById('turmaTreinamentoId');
    selectTrein.innerHTML = '<option value="">Selecione um treinamento...</option>';
    if (catalogoDeTreinamentos.length === 0) {
        await carregarCatalogo();
    }
    catalogoDeTreinamentos.forEach(t => {
        selectTrein.innerHTML += `<option value="${t.id}">${escapeHTML(t.nome)}</option>`;
    });

    // Popula o select de instrutores
    const selectInstrutor = document.getElementById('instrutorId');
    selectInstrutor.innerHTML = '<option value="">Selecione um instrutor...</option>';
    if (listaDeInstrutores.length === 0) {
        await carregarInstrutores();
    }
    listaDeInstrutores.forEach(i => {
        selectInstrutor.innerHTML += `<option value="${i.id}">${escapeHTML(i.nome)}</option>`;
    });

    // Se for edição, busca os dados da turma
    if (id) {
        try {
            const t = await chamarAPI(`/treinamentos/turmas/${id}`);
            selectTrein.value = t.treinamento_id;
            document.getElementById('dataInicio').value = t.data_inicio ? t.data_inicio.split('T')[0] : '';

            // Dispara o evento de change para atualizar a carga horária e data mínima
            selectTrein.dispatchEvent(new Event('change'));

            document.getElementById('dataFim').value = t.data_fim ? t.data_fim.split('T')[0] : '';
            document.getElementById('localRealizacao').value = t.local_realizacao || '';
            document.getElementById('instrutorId').value = t.instrutor_id || '';
            document.getElementById('horario').value = t.horario || '';

        } catch(e) {
            exibirAlerta(`Erro ao carregar dados da turma: ${e.message}`, 'danger');
            return; // Não abre o modal se houver erro
        }
    } else {
        // Se for novo
        document.getElementById('cargaHoraria').value = '';
        document.getElementById('dataFim').min = ''; // Limpa a restrição
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
        local_realizacao: document.getElementById('localRealizacao').value,
        horario: document.getElementById('horario').value,
        instrutor_id: parseInt(document.getElementById('instrutorId').value) || null
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

// NOVA FUNÇÃO: Atualiza a data de término mínima
function atualizarDataMinimaTermino() {
    const selectTreinamento = document.getElementById('turmaTreinamentoId');
    const dataInicioInput = document.getElementById('dataInicio');
    const dataFimInput = document.getElementById('dataFim');

    const selectedId = parseInt(selectTreinamento.value);
    const dataInicio = dataInicioInput.value;

    if (!selectedId || !dataInicio) {
        dataFimInput.min = '';
        return;
    }

    const treinamento = catalogoDeTreinamentos.find(t => t.id === selectedId);
    if (treinamento && treinamento.carga_horaria > 0) {
        const diasMinimos = Math.ceil(treinamento.carga_horaria / 8);

        const dataInicioObj = new Date(dataInicio + 'T00:00:00-03:00');
        const dataFimMinimaObj = new Date(dataInicioObj);
        dataFimMinimaObj.setDate(dataInicioObj.getDate() + diasMinimos - 1);

        const dataFimMinimaStr = dataFimMinimaObj.toISOString().split('T')[0];

        dataFimInput.min = dataFimMinimaStr;

        if (dataFimInput.value && dataFimInput.value < dataFimMinimaStr) {
            dataFimInput.value = dataFimMinimaStr;
        }
    } else {
        dataFimInput.min = dataInicio;
    }
}

// Carrega as inscrições de uma turma específica
async function carregarInscricoes(turmaId) {
    try {
        const inscricoes = await chamarAPI(`/treinamentos/turmas/${turmaId}/inscricoes`);
        const tbody = document.getElementById('inscricoesTableBody');
        tbody.innerHTML = '';
        if (inscricoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">Nenhuma inscrição.</td></tr>';
            return;
        }
        for (const i of inscricoes) {
            const tr = document.createElement('tr');
            tr.dataset.id = i.id;

            const statusAprovado = i.status_aprovacao === 'Aprovado' ? 'selected' : '';
            const statusReprovado = i.status_aprovacao === 'Reprovado' ? 'selected' : '';

            tr.innerHTML = `
                <td>${i.id}</td>
                <td>${escapeHTML(i.nome)}</td>
                <td>${i.cpf || ''}</td>
                <td>${i.empresa || ''}</td>
                <td>
                    <input type="number" class="form-control form-control-sm nota-teoria-input" 
                           value="${i.nota_teoria !== null ? i.nota_teoria : ''}" 
                           min="0" max="100" step="0.1">
                </td>
                <td>
                    <input type="number" class="form-control form-control-sm nota-pratica-input" 
                           value="${i.nota_pratica !== null ? i.nota_pratica : ''}" 
                           min="0" max="100" step="0.1">
                </td>
                <td>
                    <select class="form-select form-select-sm status-aprovacao-select">
                        <option value="">Selecione...</option>
                        <option value="Aprovado" ${statusAprovado}>Aprovado</option>
                        <option value="Reprovado" ${statusReprovado}>Reprovado</option>
                    </select>
                </td>
            `;
            tbody.appendChild(tr);
        }
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

// NOVA FUNÇÃO PARA SALVAR AS NOTAS
async function salvarTodasAsNotas() {
    const linhas = document.querySelectorAll('#inscricoesTableBody tr');
    const promessas = [];

    linhas.forEach(linha => {
        const id = linha.dataset.id;
        if (!id) return;

        const notaTeoria = linha.querySelector('.nota-teoria-input').value;
        const notaPratica = linha.querySelector('.nota-pratica-input').value;
        const statusAprovacao = linha.querySelector('.status-aprovacao-select').value;

        const body = {
            nota_teoria: notaTeoria,
            nota_pratica: notaPratica,
            status_aprovacao: statusAprovacao
        };

        promessas.push(chamarAPI(`/treinamentos/inscricoes/${id}/avaliar`, 'PUT', body));
    });

    try {
        await Promise.all(promessas);
        exibirAlerta('Todas as alterações foram salvas com sucesso!', 'success');
    } catch (e) {
        exibirAlerta(`Ocorreu um erro ao salvar: ${e.message}`, 'danger');
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

    const btnSalvar = document.getElementById('btnSalvarNotas');
    if (btnSalvar) {
        btnSalvar.addEventListener('click', salvarTodasAsNotas);
    }

    // Listener para o select de treinamento no modal de turma
    const selectTreinamento = document.getElementById('turmaTreinamentoId');
    const dataInicioInput = document.getElementById('dataInicio');

    if (selectTreinamento) {
        selectTreinamento.addEventListener('change', () => {
            const cargaHorariaInput = document.getElementById('cargaHoraria');
            const selectedId = parseInt(selectTreinamento.value);
            const treinamento = catalogoDeTreinamentos.find(t => t.id === selectedId);

            cargaHorariaInput.value = (treinamento && treinamento.carga_horaria) ? treinamento.carga_horaria : '';
            atualizarDataMinimaTermino();
        });
    }

    if (dataInicioInput) {
        dataInicioInput.addEventListener('change', atualizarDataMinimaTermino);
    }
});
