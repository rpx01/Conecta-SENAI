// Conteúdo completo e corrigido para o ficheiro: src/static/js/treinamentos.js

// Armazena os dados do usuário logado para reutilização
let dadosUsuarioLogado = null;

/**
 * Listener que é executado quando o conteúdo da página termina de carregar.
 * Ele verifica qual página está ativa e chama a função de carregamento correspondente.
 */
document.addEventListener('DOMContentLoaded', () => {
    // Verifica se estamos na página de Cursos Disponíveis
    if (document.getElementById('cursosContainer')) {
        carregarTreinamentos();
    }

    // Verifica se estamos na página Meus Cursos
    if (document.getElementById('listaMeusCursos')) {
        carregarMeusCursos();
    }

    // Adiciona o listener para o botão de submissão do modal de inscrição
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

    // Adiciona o listener para o checkbox de "inscrever outro"
    const checkInscreverOutro = document.getElementById('inscreverOutroCheck');
    if (checkInscreverOutro) {
        checkInscreverOutro.addEventListener('change', (e) => {
            toggleFormularioExterno(e.target.checked);
        });
    }
});

/**
 * Carrega a lista de turmas disponíveis e as exibe na página.
 */
async function carregarTreinamentos() {
    try {
        const turmas = await chamarAPI('/treinamentos');
        const container = document.getElementById('cursosContainer');
        if (!container) return;

        container.innerHTML = ''; // Limpa o spinner de carregamento
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
                                    Início: ${formatarData(t.data_inicio)} - Fim: ${formatarData(t.data_fim)}
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
        const container = document.getElementById('cursosContainer');
        if (container) container.innerHTML = '<p class="text-center text-danger">Falha ao carregar os cursos.</p>';
    }
}

/**
 * (FUNÇÃO RESTAURADA) Carrega os cursos em que o usuário está inscrito.
 */
async function carregarMeusCursos() {
    try {
        const cursos = await chamarAPI('/treinamentos/minhas');
        const ul = document.getElementById('listaMeusCursos');
        ul.innerHTML = ''; // Limpa o spinner
        if (cursos.length === 0) {
            ul.innerHTML = '<li class="list-group-item text-center">Você não está inscrito em nenhum curso.</li>';
            return;
        }
        cursos.forEach(c => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            li.textContent = `${c.treinamento.nome} - Início em ${formatarData(c.data_inicio)}`;
            ul.appendChild(li);
        });
    } catch(e) {
        exibirAlerta(e.message, 'danger');
        const ul = document.getElementById('listaMeusCursos');
        if (ul) ul.innerHTML = '<li class="list-group-item text-center text-danger">Falha ao carregar seus cursos.</li>';
    }
}

/**
 * Abre o modal de inscrição, pré-preenchendo com dados do usuário logado.
 * @param {number} turmaId - O ID da turma para a qual a inscrição será feita.
 */
async function abrirModalInscricao(turmaId) {
    try {
        if (!dadosUsuarioLogado) {
            dadosUsuarioLogado = await getUsuarioLogado();
        }

        const modalEl = document.getElementById('inscricaoModal');
        const modal = new bootstrap.Modal(modalEl);

        document.getElementById('turmaId').value = turmaId;
        document.getElementById('inscreverOutroCheck').checked = false;
        toggleFormularioExterno(false);

        modal.show();
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

/**
 * Alterna o estado do formulário de inscrição entre "para mim" e "para outro".
 * @param {boolean} isExterno - True se a inscrição for para outra pessoa.
 */
function toggleFormularioExterno(isExterno) {
    const form = document.getElementById('inscricaoForm');
    const inputs = form.querySelectorAll('input:not([type=hidden]):not([type=checkbox])');

    if (isExterno) {
        inputs.forEach(input => {
            input.readOnly = false;
            input.value = '';
        });
        document.getElementById('dataNascimento').type = 'date';
        document.getElementById('nome').focus();
    } else {
        if (dadosUsuarioLogado) {
            document.getElementById('nome').value = dadosUsuarioLogado.nome;
            document.getElementById('email').value = dadosUsuarioLogado.email;
            document.getElementById('cpf').value = dadosUsuarioLogado.cpf || '';
            document.getElementById('dataNascimento').type = 'text';
            document.getElementById('dataNascimento').value = formatarData(dadosUsuarioLogado.data_nascimento);
            document.getElementById('empresa').value = dadosUsuarioLogado.empresa || '';
        }
        inputs.forEach(input => {
            input.readOnly = true;
        });
    }
}

/**
 * Envia a inscrição para o próprio usuário logado.
 */
async function enviarInscricao() {
    const turmaId = document.getElementById('turmaId').value;
    try {
        // Para auto-inscrição, o corpo pode ser vazio, pois o backend usa o usuário da sessão.
        await chamarAPI(`/treinamentos/${turmaId}/inscricoes`, 'POST', {});
        exibirAlerta('Inscrição realizada com sucesso!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('inscricaoModal')).hide();
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}

/**
 * Envia a inscrição para um participante externo.
 */
async function enviarInscricaoExterna() {
    const turmaId = document.getElementById('turmaId').value;
    const body = {
        nome: document.getElementById('nome').value,
        email: document.getElementById('email').value,
        cpf: document.getElementById('cpf').value,
        data_nascimento: document.getElementById('dataNascimento').value,
        empresa: document.getElementById('empresa').value,
    };

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
