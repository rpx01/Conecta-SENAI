// src/static/js/treinamentos.js

// Armazena os dados do usuário logado e suas inscrições
let dadosUsuarioLogado = null;
let minhasInscricoesIds = new Set();
let contadoresIntervals = [];

/**
 * Listener que é executado quando o conteúdo da página termina de carregar.
 */
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('cursos-disponiveis-cards-container')) {
        carregarTreinamentos();
    }
    if (document.getElementById('listaMeusCursos')) {
        carregarMeusCursos();
    }

    // Listener para o botão de submissão do formulário de inscrição
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

    // Listener para o checkbox de "inscrever outro"
    const checkInscreverOutro = document.getElementById('inscreverOutroCheck');
    if (checkInscreverOutro) {
        checkInscreverOutro.addEventListener('change', (e) => {
            toggleFormularioExterno(e.target.checked);
        });
    }

    // Listener para o botão de inscrição própria no modal de seleção
    const btnParaMim = document.getElementById('btnInscreverParaMim');
    if (btnParaMim) {
        btnParaMim.addEventListener('click', async () => {
            const turmaId = document.getElementById('selecaoInscricaoModal').dataset.turmaId;
            bootstrap.Modal.getInstance(document.getElementById('selecaoInscricaoModal')).hide();

            // Volta a exibir o formulário, mas com a lógica de preenchimento corrigida
            const modalFormEl = document.getElementById('inscricaoModal');
            document.getElementById('turmaId').value = turmaId;
            document.getElementById('inscreverOutroCheck').checked = false;
            toggleFormularioExterno(false); // Esta função foi corrigida

            const modalForm = new bootstrap.Modal(modalFormEl);
            modalForm.show();
        });
    }

    // Listener para o botão de inscrição de terceiros no modal de seleção
    const btnParaOutro = document.getElementById('btnInscreverParaOutro');
    if (btnParaOutro) {
        btnParaOutro.addEventListener('click', async () => {
            const turmaId = document.getElementById('selecaoInscricaoModal').dataset.turmaId;
            bootstrap.Modal.getInstance(document.getElementById('selecaoInscricaoModal')).hide();
            
            const modalFormEl = document.getElementById('inscricaoModal');
            document.getElementById('turmaId').value = turmaId;
            document.getElementById('inscreverOutroCheck').checked = true;
            toggleFormularioExterno(true);

            const modalForm = new bootstrap.Modal(modalFormEl);
            modalForm.show();
        });
    }
});

/**
 * Carrega a lista de turmas disponíveis, verificando se o usuário já está inscrito.
 */
async function carregarTreinamentos() {
    const container = document.getElementById('cursos-disponiveis-cards-container');
    if (!container) return;

    container.innerHTML = `<div class="text-center w-100"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Carregando...</span></div></div>`;

    try {
        const [minhasInscricoes, turmas] = await Promise.all([
            chamarAPI('/treinamentos/minhas'),
            chamarAPI('/treinamentos/agendadas')
        ]);

        minhasInscricoesIds = new Set(minhasInscricoes.map(i => i.turma_id));
        container.innerHTML = '';

        if (turmas.length === 0) {
            container.innerHTML = '<p class="text-center w-100">Nenhum curso disponível no momento.</p>';
            return;
        }

        turmas.forEach(t => {
            const isInscrito = minhasInscricoesIds.has(t.turma_id);
            const botaoHtml = `<button class="btn ${isInscrito ? 'btn-success' : 'btn-primary'}" onclick="abrirModalInscricao(${t.turma_id})">${isInscrito ? '<i class="bi bi-check-circle-fill"></i> INSCRITO' : 'INSCREVER-SE'}</button>`;

            const cardHtml = `
            <div class="col">
                <div class="card h-100 curso-card-disponivel">
                    <div class="card-body">
                        <h5 class="card-title">${escapeHTML(t.treinamento.nome)}</h5>
                        <hr>
                        <div class="curso-info-item">
                            <i class="bi bi-calendar-range"></i>
                            <span><b>Período:</b> ${formatarData(t.data_inicio)} a ${formatarData(t.data_fim)}</span>
                        </div>
                        <div class="curso-info-item">
                            <i class="bi bi-person-workspace"></i>
                            <span><b>Instrutor:</b> ${escapeHTML(t.instrutor_nome)}</span>
                        </div>
                        <div class="curso-info-item">
                            <i class="bi bi-geo-alt-fill"></i>
                            <span><b>Local:</b> ${escapeHTML(t.local_realizacao)}</span>
                        </div>
                    </div>
                    <div class="card-footer bg-light">
                        <div class="d-flex justify-content-between align-items-center">
                            ${botaoHtml}
                            <div class="text-end">
                                <small class="text-muted d-block">Inscrições encerram em:</small>
                                <span class="countdown-timer" id="countdown-${t.turma_id}" data-fim="${t.data_inicio}"></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
            container.insertAdjacentHTML('beforeend', cardHtml);
        });

        iniciarContadores();

    } catch (e) {
        exibirAlerta(e.message, 'danger');
        container.innerHTML = '<p class="text-center text-danger w-100">Falha ao carregar os cursos.</p>';
    }
}

function iniciarContadores() {
    contadoresIntervals.forEach(clearInterval);
    contadoresIntervals = [];

    document.querySelectorAll('.countdown-timer').forEach(timerEl => {
        const dataFim = new Date(timerEl.dataset.fim.replace(/-/g, '/') + ' 23:59:59');

        const intervalId = setInterval(() => {
            const agora = new Date();
            const diferenca = dataFim - agora;

            if (diferenca <= 0) {
                clearInterval(intervalId);
                timerEl.textContent = 'Inscrições encerradas';
                return;
            }

            const dias = Math.floor(diferenca / (1000 * 60 * 60 * 24));
            const horas = Math.floor((diferenca % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

            timerEl.textContent = `${dias}d e ${horas}h`;
        }, 1000);
        contadoresIntervals.push(intervalId);
    });
}

/**
 * Carrega os cursos em que o usuário está inscrito.
 */
async function carregarMeusCursos() {
    const container = document.getElementById('listaMeusCursos');
    if (!container) return;

    try {
        const cursos = await chamarAPI('/treinamentos/minhas');
        minhasInscricoesIds = new Set(cursos.map(c => c.turma_id));

        container.innerHTML = '';
        if (cursos.length === 0) {
            container.innerHTML = '<div class="col-12"><p class="text-center">Você não está inscrito em nenhum curso.</p></div>';
            return;
        }

        cursos.forEach(c => {
            const hoje = new Date();
            const dataInicio = new Date(c.data_inicio);
            const dataFim = new Date(c.data_fim);

            let status = '', statusText = '', progresso = 0;

            if (hoje > dataFim) {
                status = 'concluido'; statusText = 'Concluído'; progresso = 100;
            } else if (hoje >= dataInicio) {
                status = 'em-andamento'; statusText = 'Em Andamento';
                const totalDias = (dataFim - dataInicio) / (1000 * 3600 * 24) || 1;
                const diasPassados = (hoje - dataInicio) / (1000 * 3600 * 24);
                progresso = Math.min(100, Math.round((diasPassados / totalDias) * 100));
            } else {
                status = 'futuro'; statusText = 'Em Breve'; progresso = 0;
            }

            const cardHtml = `
                <div class="col-md-6 mb-4">
                    <div class="card curso-card status-${status}" onclick="toggleDetalhes(this)">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center">
                                <h5 class="card-title mb-0">${escapeHTML(c.treinamento.nome)}</h5>
                                <span class="selo-status status-${status}">${statusText}</span>
                            </div>
                            <p class="card-text mt-2"><small class="text-muted">De ${formatarData(c.data_inicio)} a ${formatarData(c.data_fim)}</small></p>
                            <div class="progress mt-3" style="height: 10px;"><div class="progress-bar" role="progressbar" style="width: ${progresso}%;"></div></div>
                            <div class="text-center mt-3"><i class="bi bi-chevron-down"></i></div>
                            <div class="curso-detalhes">
                                <hr>
                                <h6>Descrição Completa</h6>
                                <p>${escapeHTML(c.treinamento.conteudo_programatico || 'Nenhuma descrição disponível.')}</p>
                                <h6>Instrutor</h6>
                                <p>${escapeHTML(c.instrutor ? c.instrutor.nome : 'A definir')}</p>
                                <h6>Materiais e Links</h6>
                                <ul class="lista-materiais">
                                    ${(c.treinamento.links_materiais || []).map(link => `<li><a href="${link}" target="_blank"><i class="bi bi-link-45deg"></i> Material de Apoio</a></li>`).join('') || '<li>Nenhum material disponível.</li>'}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', cardHtml);
        });
    } catch(e) {
        exibirAlerta(e.message, 'danger');
        if (container) container.innerHTML = '<div class="col-12"><p class="text-center text-danger">Falha ao carregar seus cursos.</p></div>';
    }
}

function toggleDetalhes(cardElement) {
    cardElement.classList.toggle('expandido');
}

/**
 * Abre o modal de seleção de tipo de inscrição.
 * @param {number} turmaId - O ID da turma.
 */
async function abrirModalInscricao(turmaId) {
    const btnParaMim = document.getElementById('btnInscreverParaMim');
    if (btnParaMim) {
        if (minhasInscricoesIds.has(turmaId)) {
            btnParaMim.disabled = true;
        } else {
            btnParaMim.disabled = false;
        }
    }

    const selecaoModalEl = document.getElementById('selecaoInscricaoModal');
    selecaoModalEl.dataset.turmaId = turmaId;
    const modal = new bootstrap.Modal(selecaoModalEl);
    modal.show();
}

/**
 * CORRIGIDO: Alterna a visibilidade e o estado do formulário de inscrição.
 * @param {boolean} isExterno - True se a inscrição for para outra pessoa.
 */
function toggleFormularioExterno(isExterno) {
    const form = document.getElementById('inscricaoForm');
    const inputs = form.querySelectorAll('input:not([type=hidden]):not([type=checkbox])');

    // Limpa os campos editáveis sem alterar valores ocultos ou o estado do checkbox
    inputs.forEach(input => {
        input.value = '';
        input.readOnly = false;
    });

    document.getElementById('inscreverOutroCheck').checked = isExterno;

    if (isExterno) {
        document.getElementById('dataNascimento').type = 'date';
        document.getElementById('nome').focus();
    } else {
        // Preenche com dados do usuário logado, mantendo os campos editáveis
        if (!dadosUsuarioLogado) {
            dadosUsuarioLogado = getUsuarioLogado();
        }

        if (dadosUsuarioLogado) {
            document.getElementById('nome').value = dadosUsuarioLogado.nome || '';
            document.getElementById('email').value = dadosUsuarioLogado.email || '';
        }
        document.getElementById('dataNascimento').type = 'date';
        document.getElementById('cpf').focus();
    }
}

/**
 * Envia a requisição para inscrever o próprio usuário.
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

    if (!body.nome || !body.email || !body.cpf) {
        exibirAlerta('Nome, Email e CPF são obrigatórios.', 'warning');
        return;
    }

    try {
        await chamarAPI(`/treinamentos/${turmaId}/inscricoes`, 'POST', body);
        exibirAlerta('Inscrição realizada com sucesso!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('inscricaoModal')).hide();
        
        await carregarTreinamentos();
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
