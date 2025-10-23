let modalChamado;

async function inicializarModalChamado() {
    const modalElement = document.getElementById('modalChamado');
    if (!modalElement) return;
    modalChamado = new bootstrap.Modal(modalElement);

    const usuario = getUsuarioLogado();
    const inputNome = document.getElementById('inputNome');
    const inputEmail = document.getElementById('inputEmail');
    if (usuario) {
        if (inputNome) inputNome.value = usuario.nome;
        if (inputEmail) inputEmail.value = usuario.email;
    }

    modalElement.addEventListener('show.bs.modal', () => {
        if (usuario) {
            if (inputNome) inputNome.value = usuario.nome;
            if (inputEmail && !inputEmail.value) inputEmail.value = usuario.email;
        }
    });

    document.getElementById('btnAbrirModal')?.addEventListener('click', async () => {
        await carregarDadosAuxiliares();
        modalChamado.show();
    });
}

async function carregarDadosAuxiliares() {
    try {
        const [areas, equipamentos] = await Promise.all([
            window.__suporteTI.carregarAreas(),
            window.__suporteTI.carregarEquipamentos(),
        ]);
        window.__suporteTI.preencherSelect(document.getElementById('selectArea'), areas);
        window.__suporteTI.preencherSelect(document.getElementById('selectEquipamento'), equipamentos);
    } catch (erro) {
        console.error('Erro ao carregar dados auxiliares', erro);
        showToast('Não foi possível carregar áreas e equipamentos. Tente novamente mais tarde.', 'danger');
    }
}

function validarArquivos(arquivos) {
    if (!arquivos) return true;
    const lista = Array.from(arquivos);
    if (lista.length > 5) {
        showToast('Você pode anexar no máximo 5 imagens.', 'warning');
        return false;
    }
    for (const arquivo of lista) {
        if (arquivo && arquivo.type && !arquivo.type.startsWith('image/')) {
            showToast(`Arquivo "${arquivo.name}" não é uma imagem válida.`, 'warning');
            return false;
        }
    }
    return true;
}

async function enviarChamado(evento) {
    evento.preventDefault();
    const form = evento.currentTarget;
    form.classList.add('was-validated');

    if (!form.checkValidity()) {
        showToast('Verifique os campos obrigatórios antes de enviar.', 'warning');
        return;
    }

    const inputAnexos = document.getElementById('inputAnexos');
    if (!validarArquivos(inputAnexos?.files)) {
        return;
    }

    const botaoSubmit = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);

    try {
        setBusy(botaoSubmit, true);
        await chamarAPI('/support/tickets', 'POST', formData);
        showToast('Chamado registrado com sucesso! Nossa equipe entrará em contato em breve.', 'success');
        form.reset();
        form.classList.remove('was-validated');
        const usuario = getUsuarioLogado();
        if (usuario) {
            document.getElementById('inputNome').value = usuario.nome;
            document.getElementById('inputEmail').value = usuario.email;
        }
        document.getElementById('selectUrgencia').value = '';
        if (modalChamado) {
            modalChamado.hide();
        }
    } catch (erro) {
        console.error('Falha ao registrar chamado', erro);
        const mensagem = erro?.message || 'Não foi possível registrar o chamado. Tente novamente.';
        showToast(mensagem, 'danger');
    } finally {
        setBusy(botaoSubmit, false);
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    if (!(await verificarAutenticacao())) return;
    await carregarDadosAuxiliares();
    await inicializarModalChamado();
    document.getElementById('formChamado')?.addEventListener('submit', enviarChamado);
});
