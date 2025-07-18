document.addEventListener('DOMContentLoaded', () => {
    // Validação de autenticação e permissões de administrador
    if (!verificarAutenticacao() || !isAdmin()) {
        window.location.href = '/selecao-sistema.html';
        return;
    }

    const treinamentoModal = new bootstrap.Modal(document.getElementById('treinamentoModal'));
    
    // Carrega dados iniciais
    carregarTabela();
    carregarInstrutoresNoModal();

    // Event Listeners
    document.getElementById('btn-novo-treinamento').addEventListener('click', () => {
        abrirModalParaCriar();
    });

    document.getElementById('btn-salvar-treinamento').addEventListener('click', () => {
        salvarTreinamento();
    });
});

// Abre o modal em modo de criação
function abrirModalParaCriar() {
    document.getElementById('form-treinamento').reset();
    document.getElementById('treinamentoId').value = '';
    document.getElementById('treinamentoModalLabel').textContent = 'Novo Treinamento';
    new bootstrap.Modal(document.getElementById('treinamentoModal')).show();
}

// Carrega a lista de treinamentos na tabela
async function carregarTabela() {
    const tabela = document.getElementById('tabela-catalogo');
    tabela.innerHTML = `<tr><td colspan="4" class="text-center">Carregando...</td></tr>`;
    try {
        // A API para '/api/treinamentos' precisa ser criada no backend
        // const treinamentos = await chamarAPI('/admin/treinamentos');
        
        // DADOS DE EXEMPLO ATÉ A API FICAR PRONTA
        const treinamentos = [
            { id: 1, nome: 'NR-35 Trabalho em Altura', codigo: 'TR-001', carga_horaria: 8 },
            { id: 2, nome: 'Mecânica de Usinagem', codigo: 'TR-002', carga_horaria: 40 }
        ];

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
                    <button class="btn btn-sm btn-outline-primary" title="Editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-outline-danger" title="Excluir"><i class="bi bi-trash"></i></button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        tabela.innerHTML = `<tr><td colspan="4" class="text-danger text-center">Erro ao carregar treinamentos.</td></tr>`;
    }
}

// Carrega os instrutores do banco de dados no modal
async function carregarInstrutoresNoModal() {
    const select = document.getElementById('instrutores');
    try {
        // Reutiliza a lista de instrutores do sistema de ocupação/rateio
        const instrutores = await chamarAPI('/instrutores');
        select.innerHTML = instrutores.map(i => `<option value="${i.id}">${escapeHTML(i.nome)}</option>`).join('');
    } catch (error) {
        select.innerHTML = '<option disabled>Erro ao carregar instrutores</option>';
    }
}

// Função para salvar (criar ou editar) um treinamento
async function salvarTreinamento() {
    const id = document.getElementById('treinamentoId').value;
    const dados = {
        nome: document.getElementById('nome').value,
        codigo: document.getElementById('codigo').value,
        carga_horaria: parseInt(document.getElementById('cargaHoraria').value),
        max_alunos: parseInt(document.getElementById('maxAlunos').value),
        materiais: [{
            descricao: 'Material Principal',
            url: document.getElementById('materialUrl').value
        }],
        instrutor_ids: Array.from(document.getElementById('instrutores').selectedOptions).map(opt => parseInt(opt.value))
    };

    // Validação simples
    if (!dados.nome || !dados.carga_horaria || !dados.max_alunos || dados.instrutor_ids.length === 0) {
        exibirAlerta('Preencha todos os campos obrigatórios (*).', 'warning');
        return;
    }

    const endpoint = id ? `/admin/treinamentos/${id}` : '/admin/treinamentos';
    const method = id ? 'PUT' : 'POST';

    try {
        // await chamarAPI(endpoint, method, dados); // Descomentar quando a API estiver pronta
        console.log('Dados a serem salvos:', dados); // Para teste
        
        exibirAlerta(`Treinamento ${id ? 'atualizado' : 'criado'} com sucesso! (Simulação)`, 'success');
        bootstrap.Modal.getInstance(document.getElementById('treinamentoModal')).hide();
        carregarTabela();
    } catch (error) {
        exibirAlerta(`Erro ao salvar: ${error.message}`, 'danger');
    }
}
