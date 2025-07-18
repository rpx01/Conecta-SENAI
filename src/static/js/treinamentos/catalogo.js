document.addEventListener('DOMContentLoaded', () => {
    // Validação de autenticação e permissões de administrador
    if (!verificarAutenticacao() || !isAdmin()) {
        window.location.href = '/selecao-sistema.html';
        return;
    }

    // Instancia os modais para poder controlá-los via JS
    const treinamentoModal = new bootstrap.Modal(document.getElementById('treinamentoModal'));
    const confirmacaoModal = new bootstrap.Modal(document.getElementById('confirmacaoModal'));
    let idParaExcluir = null; // Variável para guardar o ID do item a ser excluído

    // Carrega a tabela de treinamentos assim que a página é carregada
    carregarTabela();

    // Adiciona os eventos aos botões principais
    document.getElementById('btn-novo-treinamento').addEventListener('click', () => {
        abrirModalParaCriar(treinamentoModal);
    });

    document.getElementById('btn-salvar-treinamento').addEventListener('click', () => {
        salvarTreinamento(treinamentoModal);
    });

    document.getElementById('btn-confirmar-exclusao').addEventListener('click', () => {
        excluirTreinamento(idParaExcluir, confirmacaoModal);
    });

    // Usa "event delegation" para capturar cliques nos botões da tabela
    document.getElementById('tabela-catalogo').addEventListener('click', (e) => {
        const target = e.target.closest('button');
        if (!target) return;

        const treinamentoId = target.getAttribute('data-id');

        if (target.classList.contains('btn-editar')) {
            abrirModalParaEditar(treinamentoId, treinamentoModal);
        } else if (target.classList.contains('btn-excluir')) {
            const nomeTreinamento = target.getAttribute('data-nome');
            document.getElementById('nome-treinamento-excluir').textContent = nomeTreinamento;
            idParaExcluir = treinamentoId;
            confirmacaoModal.show();
        }
    });
});

/**
 * Limpa o formulário e abre o modal para um novo cadastro.
 * @param {bootstrap.Modal} modalInstance A instância do modal de treinamento.
 */
function abrirModalParaCriar(modalInstance) {
    document.getElementById('form-treinamento').reset();
    document.getElementById('treinamentoId').value = '';
    document.getElementById('treinamentoModalLabel').textContent = 'Novo Treinamento';
    modalInstance.show();
}

/**
 * Busca os dados de um treinamento específico na API e preenche o modal para edição.
 * @param {number} id O ID do treinamento a ser editado.
 * @param {bootstrap.Modal} modalInstance A instância do modal de treinamento.
 */
async function abrirModalParaEditar(id, modalInstance) {
    document.getElementById('form-treinamento').reset();
    try {
        const treinamento = await chamarAPI(`/admin/treinamentos/${id}`);
        
        document.getElementById('treinamentoId').value = treinamento.id;
        document.getElementById('nome').value = treinamento.nome;
        document.getElementById('codigo').value = treinamento.codigo;
        document.getElementById('cargaHoraria').value = treinamento.carga_horaria;
        document.getElementById('maxAlunos').value = treinamento.max_alunos;
        document.getElementById('materialUrl').value = treinamento.materiais.length > 0 ? treinamento.materiais[0].url : '';
        
        document.getElementById('treinamentoModalLabel').textContent = 'Editar Treinamento';
        modalInstance.show();
    } catch (error) {
        exibirAlerta('Não foi possível carregar os dados para edição.', 'danger');
    }
}

/**
 * Busca a lista de todos os treinamentos na API e popula a tabela.
 */
async function carregarTabela() {
    const tabela = document.getElementById('tabela-catalogo');
    tabela.innerHTML = `<tr><td colspan="4" class="text-center">Carregando...</td></tr>`;
    try {
        const treinamentos = await chamarAPI('/admin/treinamentos');

        if (treinamentos.length === 0) {
            tabela.innerHTML = `<tr><td colspan="4" class="text-center">Nenhum treinamento cadastrado.</td></tr>`;
            return;
        }

        tabela.innerHTML = treinamentos.map(t => `
            <tr>
                <td>${escapeHTML(t.nome)}</td>
                <td>${escapeHTML(t.codigo || '')}</td>
                <td>${t.carga_horaria}h</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary btn-editar" data-id="${t.id}" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-outline-danger btn-excluir" data-id="${t.id}" data-nome="${escapeHTML(t.nome)}" title="Excluir"><i class="bi bi-trash"></i></button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        tabela.innerHTML = `<tr><td colspan="4" class="text-danger text-center">Erro ao carregar treinamentos: ${error.message}</td></tr>`;
    }
}

/**
 * Coleta os dados do formulário e envia para a API para criar ou atualizar um treinamento.
 * @param {bootstrap.Modal} modalInstance A instância do modal de treinamento.
 */
async function salvarTreinamento(modalInstance) {
    const id = document.getElementById('treinamentoId').value;
    const dados = {
        nome: document.getElementById('nome').value,
        codigo: document.getElementById('codigo').value,
        carga_horaria: parseInt(document.getElementById('cargaHoraria').value),
        max_alunos: parseInt(document.getElementById('maxAlunos').value),
        materiais: [{
            descricao: 'Material Principal',
            url: document.getElementById('materialUrl').value
        }]
    };

    if (!dados.nome || !dados.carga_horaria || !dados.max_alunos) {
        exibirAlerta('Preencha todos os campos obrigatórios (*).', 'warning');
        return;
    }

    const endpoint = id ? `/admin/treinamentos/${id}` : '/admin/treinamentos';
    const method = id ? 'PUT' : 'POST';

    try {
        await chamarAPI(endpoint, method, dados);
        exibirAlerta(`Treinamento ${id ? 'atualizado' : 'criado'} com sucesso!`, 'success');
        modalInstance.hide();
        carregarTabela(); // Recarrega a tabela para mostrar a alteração
    } catch (error) {
        exibirAlerta(`Erro ao salvar: ${error.message}`, 'danger');
    }
}

/**
 * Envia uma requisição à API para excluir o treinamento selecionado.
 * @param {number} id O ID do treinamento a ser excluído.
 * @param {bootstrap.Modal} modalInstance A instância do modal de confirmação.
 */
async function excluirTreinamento(id, modalInstance) {
    try {
        await chamarAPI(`/admin/treinamentos/${id}`, 'DELETE');
        exibirAlerta('Treinamento excluído com sucesso!', 'success');
        modalInstance.hide();
        carregarTabela(); // Recarrega a tabela para remover o item
    } catch(error) {
        exibirAlerta(`Erro ao excluir: ${error.message}`, 'danger');
    }
}

