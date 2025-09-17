// Gestão de usuários com paginação
/* global bootstrap, chamarAPI, showToast, verificarAutenticacao, verificarPermissaoAdmin, escapeHTML */

function obterConfiguracaoTipoUsuario(tipo) {
    switch (tipo) {
        case 'admin':
            return { classe: 'bg-danger', rotulo: 'Administrador' };
        case 'secretaria':
            return { classe: 'bg-secondary', rotulo: 'Secretaria' };
        default:
            return { classe: 'bg-primary', rotulo: 'Comum' };
    }
}

function criarLinhaUsuario(usuario = {}) {
    const idNumerico = Number.parseInt(usuario.id, 10);
    const possuiIdValido = !Number.isNaN(idNumerico);
    const valorId = possuiIdValido ? idNumerico : '';
    const idParaAcao = possuiIdValido ? idNumerico : 'null';
    const nomeEscapado = escapeHTML(usuario.nome ?? '');
    const emailEscapado = escapeHTML(usuario.email ?? '');
    const { classe, rotulo } = obterConfiguracaoTipoUsuario(usuario.tipo);

    return `
        <tr>
            <td>${valorId}</td>
            <td>${nomeEscapado}</td>
            <td>${emailEscapado}</td>
            <td>
                <span class="badge ${classe}">
                    ${rotulo}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="editarUsuario(${idParaAcao})">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="confirmarExclusao(${idParaAcao})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `;
}

if (typeof window !== 'undefined') {
    window.__usuariosAdmin = window.__usuariosAdmin || {};
    window.__usuariosAdmin.criarLinhaUsuario = criarLinhaUsuario;
}

document.addEventListener('DOMContentLoaded', function() {
    verificarAutenticacao();
    verificarPermissaoAdmin();

    const usuarioModal = new bootstrap.Modal(document.getElementById('usuarioModal'));
    const confirmacaoModal = new bootstrap.Modal(document.getElementById('confirmacaoModal'));
    let usuarioIdParaExcluir = null;
    let paginaAtual = 1;
    const porPagina = 10;
    const paginacaoEl = document.getElementById('paginacaoUsuarios');

    carregarUsuarios();

    document.getElementById('btnSalvarUsuario').addEventListener('click', salvarUsuario);
    document.getElementById('btnConfirmarExclusao').addEventListener('click', async function() {
        if (usuarioIdParaExcluir) {
            try {
                await chamarAPI(`/usuarios/${usuarioIdParaExcluir}`, 'DELETE');
                confirmacaoModal.hide();
                showToast('Usuário excluído com sucesso!', 'success');
                carregarUsuarios(paginaAtual);
            } catch (error) {
                showToast(`Não foi possível excluir usuário: ${error.message}`, 'danger');
            }
        }
    });

    async function carregarUsuarios(page = 1) {
        try {
            const resp = await chamarAPI(`/usuarios?page=${page}&per_page=${porPagina}`);
            const usuarios = resp.items;
            const tableBody = document.getElementById('usuariosTableBody');

            if (!usuarios || usuarios.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhum usuário encontrado.</td></tr>';
                paginacaoEl.innerHTML = '';
                return;
            }

            tableBody.innerHTML = usuarios.map(criarLinhaUsuario).join('');
            paginaAtual = resp.page;
            atualizarPaginacao(resp.pages);
        } catch (error) {
            document.getElementById('usuariosTableBody').innerHTML = '<tr><td colspan="5" class="text-center text-danger">Não foi possível carregar usuários.</td></tr>';
            console.error('Não foi possível carregar usuários:', error);
        }
    }

    function atualizarPaginacao(totalPaginas) {
        paginacaoEl.innerHTML = '';
        const criarItem = (label, page, disabled = false, active = false) => {
            return `<li class="page-item ${disabled ? 'disabled' : ''} ${active ? 'active' : ''}">
                        <a class="page-link" href="#" data-page="${page}">${label}</a>
                    </li>`;
        };
        paginacaoEl.insertAdjacentHTML('beforeend', criarItem('Anterior', paginaAtual - 1, paginaAtual <= 1));
        for (let i = 1; i <= totalPaginas; i++) {
            paginacaoEl.insertAdjacentHTML('beforeend', criarItem(i, i, false, i === paginaAtual));
        }
        paginacaoEl.insertAdjacentHTML('beforeend', criarItem('Próxima', paginaAtual + 1, paginaAtual >= totalPaginas));

        Array.from(paginacaoEl.querySelectorAll('a[data-page]')).forEach(link => {
            link.addEventListener('click', e => {
                e.preventDefault();
                const alvo = parseInt(link.getAttribute('data-page'));
                if (!isNaN(alvo)) {
                    carregarUsuarios(alvo);
                }
            });
        });
    }

    async function salvarUsuario() {
        const usuarioId = document.getElementById('usuarioId').value;
        const nome = document.getElementById('nome').value;
        const email = document.getElementById('email').value;
        const senha = document.getElementById('senha').value;
        const tipo = document.getElementById('tipo').value;

        if (!nome || !email || (!usuarioId && !senha)) {
            showToast('Preencha todos os campos obrigatórios', 'warning');
            return;
        }

        try {
            const dadosUsuario = { nome, email, tipo };
            if (senha) {
                dadosUsuario.senha = senha;
            }

            if (usuarioId) {
                await chamarAPI(`/usuarios/${usuarioId}`, 'PUT', dadosUsuario);
                showToast('Usuário atualizado com sucesso!', 'success');
            } else {
                await chamarAPI('/usuarios', 'POST', dadosUsuario);
                showToast('Usuário criado com sucesso!', 'success');
            }

            usuarioModal.hide();
            carregarUsuarios(paginaAtual);

            document.getElementById('usuarioForm').reset();
            document.getElementById('usuarioId').value = '';
        } catch (error) {
            showToast(`Não foi possível salvar usuário: ${error.message}`, 'danger');
        }
    }

    window.editarUsuario = async function(id) {
        try {
            const usuario = await chamarAPI(`/usuarios/${id}`);
            document.getElementById('usuarioId').value = usuario.id;
            document.getElementById('nome').value = usuario.nome;
            document.getElementById('email').value = usuario.email;
            document.getElementById('senha').value = '';
            document.getElementById('tipo').value = usuario.tipo;
            document.getElementById('usuarioModalLabel').textContent = 'Editar Usuário';
            document.getElementById('senhaHelp').style.display = 'block';
            usuarioModal.show();
        } catch (error) {
            showToast(`Não foi possível carregar dados do usuário: ${error.message}`, 'danger');
        }
    };

    window.confirmarExclusao = function(id) {
        usuarioIdParaExcluir = id;
        confirmacaoModal.show();
    };

    document.getElementById('usuarioModal').addEventListener('hidden.bs.modal', function() {
        document.getElementById('usuarioForm').reset();
        document.getElementById('usuarioId').value = '';
        document.getElementById('usuarioModalLabel').textContent = 'Novo Usuário';
        document.getElementById('senhaHelp').style.display = 'none';
    });
});

