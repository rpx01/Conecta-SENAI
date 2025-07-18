document.addEventListener('DOMContentLoaded', () => {
    if (!verificarAutenticacao() || !isAdmin()) {
        window.location.href = '/selecao-sistema.html';
        return;
    }

    const treinamentoModal = new bootstrap.Modal(document.getElementById('treinamentoModal'));
    
    carregarTabela();

    document.getElementById('btn-novo-treinamento').addEventListener('click', () => {
        abrirModalParaCriar(treinamentoModal);
    });

    document.getElementById('btn-salvar-treinamento').addEventListener('click', () => {
        salvarTreinamento(treinamentoModal);
    });
});

function abrirModalParaCriar(modalInstance) {
    document.getElementById('form-treinamento').reset();
    document.getElementById('treinamentoId').value = '';
    document.getElementById('treinamentoModalLabel').textContent = 'Novo Treinamento';
    modalInstance.show();
}

async function carregarTabela() {
    const tabela = document.getElementById('tabela-catalogo');
    tabela.innerHTML = `<tr><td colspan="4" class="text-center">Carregando...</td></tr>`;
    try {
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

async function salvarTreinamento(modalInstance) {
    const id = document.getElementById('treinamentoId').value;
    const dados = {
        nome: document.getElementById('nome').value,
        codigo: document.getElementById('codigo').value,
        carga_horaria: parseInt(document.getElementById('cargaHoraria').value),
        materiais: [{
            descricao: 'Material Principal',
            url: document.getElementById('materialUrl').value
        }]
    };

    if (!dados.nome || !dados.carga_horaria) {
        exibirAlerta('Preencha os campos obrigatórios (*).', 'warning');
        return;
    }

    exibirAlerta(`Treinamento ${id ? 'atualizado' : 'criado'} com sucesso! (Simulação)`, 'success');
    modalInstance.hide();
    carregarTabela();
}
