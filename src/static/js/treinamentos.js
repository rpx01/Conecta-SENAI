// Armazena os dados do usuário logado para reutilização
let dadosUsuarioLogado = null;

document.addEventListener('DOMContentLoaded', () => {
    carregarTreinamentos();

    const btnEnviar = document.getElementById('btnEnviarInscricao');
    if (btnEnviar) {
        btnEnviar.addEventListener('click', () => {
            const isInscreverOutro = document.getElementById('inscreverOutroCheck').checked;
            if (isInscreverOutro) {
                enviarInscricaoExterna();
            } else {
                enviarInscricao();
            }
        });
    }

    const checkInscreverOutro = document.getElementById('inscreverOutroCheck');
    if (checkInscreverOutro) {
        checkInscreverOutro.addEventListener('change', (e) => {
            toggleFormularioExterno(e.target.checked);
        });
    }
});

async function carregarTreinamentos() {
    try {
        const turmas = await chamarAPI('/treinamentos');
        const container = document.getElementById('cursosContainer');
        if (!container) return;

        container.innerHTML = '';
        if (turmas.length === 0) {
            container.innerHTML = '<p class="text-center">Nenhum curso disponível no momento.</p>';
            return;
        }

        turmas.forEach(t => {
            const card = `
                <div class="col-md-6 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">${escapeHTML(t.treinamento.nome)}</h5>
                            <p class="card-text">${escapeHTML(t.treinamento.descricao || '')}</p>
                            <p class="card-text">
                                <small class="text-muted">
                                    Início: ${formatarData(t.data_inicio)}
                                </small>
                            </p>
                            <button class="btn btn-primary" onclick="abrirModalInscricao(${t.turma_id})">
                                INSCREVER-SE
                            </button>
                        </div>
                    </div>
                </div>`;
            container.innerHTML += card;
        });
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

async function abrirModalInscricao(turmaId) {
    try {
        // Guarda os dados do usuário logado se ainda não tivermos
        if (!dadosUsuarioLogado) {
            dadosUsuarioLogado = await getUsuarioLogado();
        }

        const modalEl = document.getElementById('inscricaoModal');
        const modal = new bootstrap.Modal(modalEl);

        document.getElementById('turmaId').value = turmaId;

        // Redefine o formulário para o estado padrão (inscrever a si mesmo)
        document.getElementById('inscreverOutroCheck').checked = false;
        toggleFormularioExterno(false);

        modal.show();
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

function toggleFormularioExterno(isExterno) {
    const form = document.getElementById('inscricaoForm');
    const inputs = form.querySelectorAll('input:not([type=hidden]):not([type=checkbox])');

    if (isExterno) {
        // Habilita e limpa os campos para inserir dados de outra pessoa
        inputs.forEach(input => {
            input.readOnly = false;
            input.value = '';
        });
        // A data de nascimento deve ser do tipo date
        document.getElementById('dataNascimento').type = 'date';
        // Foca no primeiro campo
        document.getElementById('nome').focus();
    } else {
        // Preenche os campos com os dados do usuário logado e os desabilita
        if (dadosUsuarioLogado) {
            document.getElementById('nome').value = dadosUsuarioLogado.nome;
            document.getElementById('email').value = dadosUsuarioLogado.email;
            document.getElementById('cpf').value = dadosUsuarioLogado.cpf;
            document.getElementById('dataNascimento').type = 'text';
            document.getElementById('dataNascimento').value = formatarData(dadosUsuarioLogado.data_nascimento);
            document.getElementById('empresa').value = dadosUsuarioLogado.empresa;
        }
        inputs.forEach(input => {
            input.readOnly = true;
        });
    }
}

async function enviarInscricao() {
    const turmaId = document.getElementById('turmaId').value;
    try {
        await chamarAPI(`/treinamentos/${turmaId}/inscricoes`, 'POST');
        exibirAlerta('Inscrição realizada com sucesso!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('inscricaoModal')).hide();
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

async function enviarInscricaoExterna() {
    const turmaId = document.getElementById('turmaId').value;
    const body = {
        nome: document.getElementById('nome').value,
        email: document.getElementById('email').value,
        cpf: document.getElementById('cpf').value,
        data_nascimento: document.getElementById('dataNascimento').value,
        empresa: document.getElementById('empresa').value,
    };

    // Validação simples
    if (!body.nome || !body.email || !body.cpf) {
        exibirAlerta('Nome, Email e CPF são obrigatórios.', 'warning');
        return;
    }

    try {
        await chamarAPI(`/treinamentos/${turmaId}/inscricoes/externo`, 'POST', body);
        exibirAlerta('Inscrição para o participante externo realizada com sucesso!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('inscricaoModal')).hide();
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}
