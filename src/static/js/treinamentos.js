// src/static/js/treinamentos.js

// Armazena os dados do usuário logado para reutilização
let dadosUsuarioLogado = null;

/**
 * Listener que é executado quando o conteúdo da página termina de carregar.
 * Ele verifica qual página está ativa e chama a função de carregamento correspondente.
 */
document.addEventListener('DOMContentLoaded', () => {
    // Verifica se estamos na página de Cursos Disponíveis
    if (document.getElementById('listaTreinamentos')) {
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
            const isExterno = document.getElementById('inscreverOutroCheck').checked;
            if (isExterno) {
                enviarInscricaoExterna();
            } else {
                enviarInscricaoPropria();
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

    // Listener para o botão de inscrição própria
    const btnParaMim = document.getElementById('btnInscreverParaMim');
    if (btnParaMim) {
        btnParaMim.addEventListener('click', async () => {
            const turmaId = document.getElementById('selecaoInscricaoModal').dataset.turmaId;
            bootstrap.Modal.getInstance(document.getElementById('selecaoInscricaoModal')).hide();

            if (!dadosUsuarioLogado) {
                dadosUsuarioLogado = await getUsuarioLogado();
            }

            const modalFormEl = document.getElementById('inscricaoModal');
            document.getElementById('turmaId').value = turmaId;

            // Configura o formulário para inscrição própria
            document.getElementById('inscreverOutroCheck').checked = false;
            toggleFormularioExterno(false);

            const modalForm = new bootstrap.Modal(modalFormEl);
            modalForm.show();
        });
    }

    // Listener para o botão de inscrição de terceiros
    const btnParaOutro = document.getElementById('btnInscreverParaOutro');
    if (btnParaOutro) {
        btnParaOutro.addEventListener('click', async () => {
            const turmaId = document.getElementById('selecaoInscricaoModal').dataset.turmaId;
            bootstrap.Modal.getInstance(document.getElementById('selecaoInscricaoModal')).hide();

            const modalFormEl = document.getElementById('inscricaoModal');
            document.getElementById('turmaId').value = turmaId;

            // Força a visualização para inscrição de terceiros
            document.getElementById('inscreverOutroCheck').checked = true;
            toggleFormularioExterno(true);

            const modalForm = new bootstrap.Modal(modalFormEl);
            modalForm.show();
        });
    }
});

/**
 * Carrega a lista de turmas disponíveis e as exibe na página.
 */
async function carregarTreinamentos() {
    try {
        const turmas = await chamarAPI('/treinamentos/agendadas');
        const container = document.getElementById('listaTreinamentos');
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
        const container = document.getElementById('listaTreinamentos');
        if (container) container.innerHTML = '<p class="text-center text-danger">Falha ao carregar os cursos.</p>';
    }
}

/**
 * Carrega os cursos em que o usuário está inscrito.
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
 * Abre o modal inicial de seleção de tipo de inscrição.
 * @param {number} turmaId - O ID da turma para a qual a inscrição será feita.
 */
async function abrirModalInscricao(turmaId) {
    const selecaoModalEl = document.getElementById('selecaoInscricaoModal');
    selecaoModalEl.dataset.turmaId = turmaId; // Armazena o ID da turma no modal

    const modal = new bootstrap.Modal(selecaoModalEl);
    modal.show();
}

/**
 * Alterna a visibilidade e o estado do formulário de inscrição.
 * @param {boolean} isExterno - True se a inscrição for para outra pessoa.
 */
function toggleFormularioExterno(isExterno) {
    const form = document.getElementById('inscricaoForm');
    const nomeInput = document.getElementById('nome');
    const emailInput = document.getElementById('email');
    const cpfInput = document.getElementById('cpf');
    const empresaInput = document.getElementById('empresa');
    const dataNascimentoInput = document.getElementById('dataNascimento');

    if (isExterno) {
        // Limpa e habilita todos os campos para inscrição de terceiros
        form.reset();
        const inputs = form.querySelectorAll('input:not([type=hidden]):not([type=checkbox])');
        inputs.forEach(input => input.readOnly = false);
        dataNascimentoInput.type = 'date';
        nomeInput.focus();
    } else {
        // Preenche os campos para inscrição própria e bloqueia apenas os que já têm dados
        if (dadosUsuarioLogado) {
            nomeInput.value = dadosUsuarioLogado.nome || '';
            nomeInput.readOnly = !!dadosUsuarioLogado.nome;

            emailInput.value = dadosUsuarioLogado.email || '';
            emailInput.readOnly = !!dadosUsuarioLogado.email;

            cpfInput.value = dadosUsuarioLogado.cpf || '';
            cpfInput.readOnly = !!dadosUsuarioLogado.cpf;

            empresaInput.value = dadosUsuarioLogado.empresa || '';
            empresaInput.readOnly = !!dadosUsuarioLogado.empresa;

            // Trata o campo de data de nascimento de forma especial
            if (dadosUsuarioLogado.data_nascimento) {
                dataNascimentoInput.type = 'text';
                dataNascimentoInput.value = formatarData(dadosUsuarioLogado.data_nascimento);
                dataNascimentoInput.readOnly = true;
            } else {
                dataNascimentoInput.type = 'date';
                dataNascimentoInput.value = '';
                dataNascimentoInput.readOnly = false;
            }
        }
    }
}

/**
 * Envia a requisição para inscrever o próprio usuário, usando os dados do formulário.
 */
async function enviarInscricaoPropria() {
    const turmaId = document.getElementById('turmaId').value;
    const body = {
        nome: document.getElementById('nome').value,
        email: document.getElementById('email').value,
        cpf: document.getElementById('cpf').value,
        data_nascimento: document.getElementById('dataNascimento').value,
        empresa: document.getElementById('empresa').value,
    };

    if (!body.nome || !body.email || !body.cpf || !body.data_nascimento) {
        exibirAlerta('Nome, Email, CPF e Data de Nascimento são obrigatórios.', 'warning');
        return;
    }

    try {
        await chamarAPI(`/treinamentos/${turmaId}/inscricoes`, 'POST', body);
        exibirAlerta('Inscrição realizada com sucesso!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('inscricaoModal')).hide();

        if (document.getElementById('listaMeusCursos')) {
            carregarMeusCursos();
        }
    } catch (e) {
        exibirAlerta(e.message, 'danger');
    }
}


/**
 * Envia a requisição para inscrever um participante externo.
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
