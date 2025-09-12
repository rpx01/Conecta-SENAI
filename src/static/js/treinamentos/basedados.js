/* global chamarAPI, showToast, escapeHTML, executarAcaoComFeedback, bootstrap */

let contatosSecretaria = [];

async function carregarContatosSecretaria() {
    try {
        const dados = await chamarAPI('/treinamentos/secretaria');
        contatosSecretaria = dados;
        const tbody = document.getElementById('secretariaTableBody');
        if (!tbody) return;
        tbody.innerHTML = '';
        if (!dados.length) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">Nenhum contato cadastrado.</td></tr>';
            return;
        }
        for (const item of dados) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.id}</td>
                <td>${escapeHTML(item.nome)}</td>
                <td>${escapeHTML(item.email)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="abrirModalSecretaria(${item.id})"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-outline-danger" onclick="excluirContatoSecretaria(${item.id})"><i class="bi bi-trash"></i></button>
                </td>`;
            tbody.appendChild(tr);
        }
    } catch (e) {
        showToast(e.message, 'danger');
    }
}

function abrirModalSecretaria(id = null) {
    const form = document.getElementById('secretariaForm');
    form.reset();
    document.getElementById('secretariaId').value = '';
    if (id) {
        const item = contatosSecretaria.find(c => c.id === id);
        if (item) {
            document.getElementById('secretariaId').value = item.id;
            document.getElementById('secretariaNome').value = item.nome;
            document.getElementById('secretariaEmail').value = item.email;
        }
    }
    const modalEl = document.getElementById('secretariaModal');
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
}

async function salvarContatoSecretaria() {
    const id = document.getElementById('secretariaId').value;
    const body = {
        nome: document.getElementById('secretariaNome').value,
        email: document.getElementById('secretariaEmail').value,
    };
    const btn = document.querySelector('button[form="secretariaForm"]');
    await executarAcaoComFeedback(btn, async () => {
        try {
            const endpoint = id ? `/treinamentos/secretaria/${id}` : '/treinamentos/secretaria';
            const method = id ? 'PUT' : 'POST';
            await chamarAPI(endpoint, method, body);
            bootstrap.Modal.getInstance(document.getElementById('secretariaModal')).hide();
            await carregarContatosSecretaria();
        } catch (e) {
            showToast(e.message, 'danger');
            throw e;
        }
    });
}

async function excluirContatoSecretaria(id) {
    if (!confirm('Excluir contato?')) return;
    try {
        await chamarAPI(`/treinamentos/secretaria/${id}`, 'DELETE');
        await carregarContatosSecretaria();
    } catch (e) {
        showToast(e.message, 'danger');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('secretariaForm');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            salvarContatoSecretaria();
        });
    }
    carregarContatosSecretaria();
});

window.abrirModalSecretaria = abrirModalSecretaria;
window.excluirContatoSecretaria = excluirContatoSecretaria;
