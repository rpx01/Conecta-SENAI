// Gerenciamento de turmas utilizando função genérica de tabela

document.addEventListener('DOMContentLoaded', () => {
    verificarAutenticacao();
    verificarPermissaoAdmin();

    const confirmacaoModal = new bootstrap.Modal(document.getElementById('confirmacaoModal'));
    let turmaParaExcluir = null;

    function renderizarLinhaTurma(turma) {
        return `
            <tr>
                <td>${turma.id}</td>
                <td>${escapeHTML(turma.nome)}</td>
                <td>${formatarData(turma.data_criacao)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editarTurma(${turma.id}, '${escapeHTML(turma.nome)}')">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="confirmarExclusao(${turma.id}, '${escapeHTML(turma.nome)}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }

    async function carregarTurmas() {
        await preencherTabela('turmasTable', '/turmas', renderizarLinhaTurma);
    }

    document.getElementById('turmaForm').addEventListener('submit', function(e) {
        e.preventDefault();
        salvarTurma();
    });

    document.getElementById('btnConfirmarExclusao').addEventListener('click', function() {
        if (turmaParaExcluir !== null) {
            excluirTurma(turmaParaExcluir);
        }
        confirmacaoModal.hide();
    });

    async function salvarTurma() {
        const btn = document.getElementById('btnSalvarTurma');
        const spinner = btn ? btn.querySelector('.spinner-border') : null;
        if (btn && spinner) {
            btn.disabled = true;
            spinner.classList.remove('d-none');
        }
        const id = document.getElementById('turmaId').value;
        const nome = document.getElementById('nomeTurma').value;

        if (!nome) {
            exibirAlerta('O nome da turma é obrigatório.', 'danger');
            return;
        }

        try {
            if (id) {
                await chamarAPI(`/turmas/${id}`, 'PUT', { nome });
                exibirAlerta('Turma atualizada com sucesso!', 'success');
            } else {
                await chamarAPI('/turmas', 'POST', { nome });
                exibirAlerta('Turma cadastrada com sucesso!', 'success');
            }

            document.getElementById('turmaForm').reset();
            document.getElementById('turmaId').value = '';
            document.getElementById('btnSalvarTurma').innerHTML = '<i class="bi bi-plus-circle me-2"></i>Adicionar';
            carregarTurmas();
        } catch (error) {
            exibirAlerta(`Erro ao salvar turma: ${error.message}`, 'danger');
        } finally {
            if (btn && spinner) {
                btn.disabled = false;
                spinner.classList.add('d-none');
            }
        }
    }

    window.editarTurma = function(id, nome) {
        document.getElementById('turmaId').value = id;
        document.getElementById('nomeTurma').value = nome;
        document.getElementById('btnSalvarTurma').innerHTML = '<i class="bi bi-check-circle me-2"></i>Atualizar';
        document.getElementById('nomeTurma').focus();
    };

    window.confirmarExclusao = function(id, nome) {
        turmaParaExcluir = id;
        document.getElementById('confirmacaoModalBody').innerHTML = `
            <p>Tem certeza que deseja excluir a turma "${escapeHTML(nome)}"?</p>
            <p class="text-danger">Esta ação não pode ser desfeita.</p>
        `;
        confirmacaoModal.show();
    };

    async function excluirTurma(id) {
        try {
            await chamarAPI(`/turmas/${id}`, 'DELETE');
            exibirAlerta('Turma excluída com sucesso!', 'success');
            carregarTurmas();
        } catch (error) {
            exibirAlerta(`Erro ao excluir turma: ${error.message}`, 'danger');
        }
    }

    carregarTurmas();
});
