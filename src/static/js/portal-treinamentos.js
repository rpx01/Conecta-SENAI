document.addEventListener('DOMContentLoaded', () => {
    // Garante que o usuário está autenticado
    if (!verificarAutenticacao()) return;

    const usuario = getUsuarioLogado();
    if (usuario) {
        document.getElementById('userName').textContent = usuario.nome;
        if (isAdmin()) {
            document.querySelectorAll('.admin-only').forEach(el => {
                el.style.display = 'list-item';
            });
        }
    }

    carregarTurmasDisponiveis();
});

async function carregarTurmasDisponiveis() {
    const container = document.getElementById('lista-treinamentos');
    if (!container) return;

    container.innerHTML = `<div class="text-center"><div class="spinner-border text-primary"></div></div>`;

    try {
        const turmas = await chamarAPI('/turmas_disponiveis');
        if (!turmas || turmas.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">Nenhum treinamento disponível no momento.</p>';
            return;
        }

        let html = '';
        turmas.forEach(turma => {
            const instrutores = turma.instrutores.map(i => i.nome).join(', ') || 'A definir';
            html += `
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card h-100 shadow-sm">
                        <div class="card-body d-flex flex-column">
                            <h5 class="card-title">${escapeHTML(turma.treinamento_nome)}</h5>
                            <p class="card-text text-muted">
                                <i class="bi bi-calendar-event"></i> Início em: ${formatarData(turma.data_inicio)} <br>
                                <i class="bi bi-person-badge"></i> Instrutor(es): ${escapeHTML(instrutores)}
                            </p>
                            <button class="btn btn-primary mt-auto" onclick="inscreverNaTurma(${turma.id})">
                                <i class="bi bi-check-circle-fill me-2"></i>Inscrever-se
                            </button>
                        </div>
                    </div>
                </div>`;
        });
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<p class="text-danger text-center">Erro ao carregar treinamentos: ${escapeHTML(error.message)}</p>`;
    }
}

async function inscreverNaTurma(turmaId) {
    try {
        await chamarAPI('/turmas/inscrever', 'POST', { turma_id: turmaId });
        exibirAlerta('Inscrição realizada com sucesso!', 'success');
    } catch (error) {
        exibirAlerta(error.message, 'danger');
    }
}
