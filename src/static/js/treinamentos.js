async function carregarTreinamentos() {
    try {
        const dados = await chamarAPI('/treinamentos');
        const container = document.getElementById('listaTreinamentos');
        container.innerHTML = '';
        dados.forEach(t => {
            const div = document.createElement('div');
            div.className = 'card mb-3';
            div.innerHTML = `<div class="card-body">
                <h5 class="card-title">${escapeHTML(t.treinamento.nome)}</h5>
                <p class="card-text">Início: ${formatarData(t.data_inicio)} - Término: ${formatarData(t.data_termino)}</p>
                <button class="btn btn-primary" data-id="${t.turma_id}">Inscrever-se</button>
            </div>`;
            container.appendChild(div);
        });
        container.addEventListener('click', function(e){
            if(e.target.tagName === 'BUTTON') {
                abrirModalInscricao(e.target.dataset.id);
            }
        });
    } catch(e) {
        exibirAlerta(e.message, 'danger');
    }
}

function abrirModalInscricao(turmaId) {
    const usuario = getUsuarioLogado();
    document.getElementById('turmaId').value = turmaId;
    document.getElementById('nome').value = usuario?.nome || '';
    document.getElementById('email').value = usuario?.email || '';
    document.getElementById('cpf').value = usuario?.cpf || '';
    document.getElementById('data_nascimento').value = usuario?.data_nascimento || '';
    document.getElementById('empresa').value = usuario?.empresa || '';
    new bootstrap.Modal(document.getElementById('inscricaoModal')).show();
}

async function enviarInscricao() {
    const turmaId = document.getElementById('turmaId').value;
    const body = {
        nome: document.getElementById('nome').value,
        email: document.getElementById('email').value,
        cpf: document.getElementById('cpf').value,
        data_nascimento: document.getElementById('data_nascimento').value,
        empresa: document.getElementById('empresa').value
    };
    try {
        await chamarAPI(`/treinamentos/${turmaId}/inscricoes`, 'POST', body);
        exibirAlerta('Inscrição realizada com sucesso', 'success');
        bootstrap.Modal.getInstance(document.getElementById('inscricaoModal')).hide();
    } catch(e) {
        exibirAlerta(e.message, 'danger');
    }
}

async function carregarMeusCursos() {
    try {
        const cursos = await chamarAPI('/treinamentos/minhas');
        const ul = document.getElementById('listaMeusCursos');
        ul.innerHTML = '';
        cursos.forEach(c => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            li.textContent = `${c.treinamento.nome} - início ${formatarData(c.data_inicio)}`;
            ul.appendChild(li);
        });
    } catch(e) {
        exibirAlerta(e.message, 'danger');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('listaTreinamentos')) {
        carregarTreinamentos();
    }
    if (document.getElementById('listaMeusCursos')) {
        carregarMeusCursos();
    }
});
