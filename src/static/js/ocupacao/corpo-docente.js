class GerenciadorInstrutores {
    constructor() {
        this.instrutores = [];
        this.instrutorAtual = null;
        this.instrutorParaExcluir = null;

        this.tabelaBody = document.getElementById('tabelaCorpoDocente');
        this.btnAdicionar = document.getElementById('btnAdicionarNovo');
        this.btnAplicarFiltros = document.getElementById('btnAplicarFiltros');
        this.btnLimparFiltros = document.getElementById('btnLimparFiltros');
        this.filtroNome = document.getElementById('filtroNome');
        this.filtroStatus = document.getElementById('filtroStatus');
        this.modalEl = document.getElementById('modalInstrutor');
        this.modalInstrutor = new bootstrap.Modal(this.modalEl);
        this.modalExcluir = new bootstrap.Modal(document.getElementById('modalExcluirInstrutor'));
        this.form = document.getElementById('formInstrutor');
        this.btnSalvar = document.getElementById('btnSalvarInstrutor');

        this.registrarEventos();
        this.carregarAreas();
        this.carregarInstrutores();
    }

    registrarEventos() {
        this.btnAdicionar.addEventListener('click', () => this.novoInstrutor());
        if (this.btnAplicarFiltros) {
            this.btnAplicarFiltros.addEventListener('click', () => this.aplicarFiltros());
        }
        if (this.btnLimparFiltros) {
            this.btnLimparFiltros.addEventListener('click', () => this.limparFiltros());
        }
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.salvarInstrutor();
        });
        this.tabelaBody.addEventListener('click', (e) => {
            const editBtn = e.target.closest('.btn-editar');
            const delBtn = e.target.closest('.btn-excluir');
            if (editBtn) {
                const id = editBtn.closest('tr').dataset.id;
                this.abrirEdicao(id);
            }
            if (delBtn) {
                const row = delBtn.closest('tr');
                const id = row.dataset.id;
                const nome = row.querySelector('td').textContent.trim();
                this.excluirInstrutor(id, nome);
            }
        });
        document.getElementById('confirmarExcluirInstrutor')
            .addEventListener('click', () => this.confirmarExclusao());

        // Adiciona o listener para limpar o formulário sempre que o modal for fechado
        this.modalEl.addEventListener('hidden.bs.modal', () => {
            this.form.reset();
            document.getElementById('instrutorId').value = '';
            this.instrutorAtual = null;
        });
    }

    async carregarAreas() {
        try {
            const areas = await chamarAPI('/instrutores/areas-atuacao');
            const select = document.getElementById('instrutorArea');
            select.innerHTML = '<option value="">Selecione...</option>';
            areas.forEach(a => {
                const opt = document.createElement('option');
                opt.value = a.valor;
                opt.textContent = a.nome;
                select.appendChild(opt);
            });
        } catch (e) {
            console.error('Erro ao carregar áreas', e);
        }
    }



    badgesDisponibilidade(list) {
        const disp = list || [];
        return `
            <span class="badge ${disp.includes('manha') ? 'bg-success' : 'bg-light text-dark'}">M</span>
            <span class="badge ${disp.includes('tarde') ? 'bg-success' : 'bg-light text-dark'}">T</span>
            <span class="badge ${disp.includes('noite') ? 'bg-success' : 'bg-light text-dark'}">N</span>
        `;
    }

    renderizarTabela(lista = this.instrutores) {
        this.tabelaBody.innerHTML = '';
        lista.forEach(inst => {
            const row = document.createElement('tr');
            row.dataset.id = inst.id;
            row.innerHTML = `
                <td><strong>${escapeHTML(inst.nome)}</strong><br><small class="text-muted">${escapeHTML(inst.email || '')}</small></td>
                <td>${escapeHTML(inst.area_atuacao || '')}</td>
                <td><span class="badge ${inst.status === 'ativo' ? 'bg-success' : 'bg-secondary'}">${inst.status}</span></td>
                <td><div class="d-flex gap-1">${this.badgesDisponibilidade(inst.disponibilidade)}</div></td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary btn-editar"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-outline-danger btn-excluir"><i class="bi bi-trash"></i></button>
                </td>`;
            this.tabelaBody.appendChild(row);
        });
    }

    async carregarInstrutores() {
        try {
            const dados = await chamarAPI('/instrutores');
            this.instrutores = dados;
            this.renderizarTabela();
        } catch (err) {
            showToast('Não foi possível carregar os instrutores.', 'danger');
        }
    }

    aplicarFiltros() {
        const termo = (this.filtroNome.value || '').toLowerCase();
        const status = this.filtroStatus.value;
        const filtrados = this.instrutores.filter(i => {
            const matchNome = i.nome.toLowerCase().includes(termo);
            const matchStatus = !status || i.status === status;
            return matchNome && matchStatus;
        });
        this.renderizarTabela(filtrados);
    }

    limparFiltros() {
        if (this.filtroNome) this.filtroNome.value = '';
        if (this.filtroStatus) this.filtroStatus.value = '';
        this.renderizarTabela();
    }

    novoInstrutor() {
        this.instrutorAtual = null;
        this.form.reset();
        document.getElementById('instrutorId').value = '';
        document.getElementById('modalInstrutorLabel').textContent = 'Novo Instrutor';
        this.btnSalvar.querySelector('.btn-text').textContent = 'Salvar';
        this.modalInstrutor.show();
    }

    preencherFormulario(instr) {
        document.getElementById('instrutorId').value = instr.id;
        document.getElementById('instrutorNome').value = instr.nome || '';
        document.getElementById('instrutorEmail').value = instr.email || '';
        document.getElementById('instrutorArea').value = instr.area_atuacao || '';
        document.getElementById('instrutorStatus').value = instr.status || 'ativo';
        document.getElementById('instrutorObservacoes').value = instr.observacoes || '';


        const disp = instr.disponibilidade || [];
        document.getElementById('dispManha').checked = disp.includes('manha');
        document.getElementById('dispTarde').checked = disp.includes('tarde');
        document.getElementById('dispNoite').checked = disp.includes('noite');
    }

    async abrirEdicao(id) {
        try {
            const instrutor = await chamarAPI(`/instrutores/${id}`);
            this.instrutorAtual = instrutor;
            this.preencherFormulario(instrutor);
            document.getElementById('modalInstrutorLabel').textContent = 'Editar Instrutor';
            this.btnSalvar.querySelector('.btn-text').textContent = 'Atualizar';
            this.modalInstrutor.show();
        } catch (e) {
            showToast('Não foi possível carregar os dados do instrutor.', 'danger');
        }
    }

    coletarFormData() {
        const formData = {
            nome: document.getElementById('instrutorNome').value.trim(),
            email: document.getElementById('instrutorEmail').value.trim(),
            area_atuacao: document.getElementById('instrutorArea').value,
            status: document.getElementById('instrutorStatus').value,
            observacoes: document.getElementById('instrutorObservacoes').value.trim(),
            disponibilidade: []
        };
        if (document.getElementById('dispManha').checked) formData.disponibilidade.push('manha');
        if (document.getElementById('dispTarde').checked) formData.disponibilidade.push('tarde');
        if (document.getElementById('dispNoite').checked) formData.disponibilidade.push('noite');
        return formData;
    }

    async salvarInstrutor() {
        const dados = this.coletarFormData();
        if (!dados.nome || !dados.email) {
            showToast('Por favor, preencha o nome e o e-mail.', 'warning');
            return;
        }
        const spinner = this.btnSalvar.querySelector('.spinner-border');
        this.btnSalvar.disabled = true;
        spinner.classList.remove('d-none');

        const isEdicao = !!this.instrutorAtual;
        const endpoint = isEdicao ? `/instrutores/${this.instrutorAtual.id}` : '/instrutores';
        const method = isEdicao ? 'PUT' : 'POST';
        try {
            await chamarAPI(endpoint, method, dados);
            showToast(`Instrutor ${isEdicao ? 'atualizado' : 'cadastrado'} com sucesso!`, 'success');
            this.modalInstrutor.hide();
            this.carregarInstrutores();
        } catch (e) {
            showToast(`Não foi possível salvar o instrutor: ${e.message}`, 'danger');
        } finally {
            this.btnSalvar.disabled = false;
            spinner.classList.add('d-none');
        }
    }

    excluirInstrutor(id, nome) {
        this.instrutorParaExcluir = id;
        document.getElementById('nomeInstrutorExcluir').textContent = nome;
        this.modalExcluir.show();
    }

    async confirmarExclusao() {
        try {
            await chamarAPI(`/instrutores/${this.instrutorParaExcluir}`, 'DELETE');
            showToast('Instrutor excluído com sucesso!', 'success');
            this.modalExcluir.hide();
            this.carregarInstrutores();
        } catch (e) {
            showToast(`Não foi possível excluir o instrutor: ${e.message}`, 'danger');
        }
    }
}

function loadUsers() {
    fetch('/api/ocupacao/users')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('corpo-docente-tbody');
            tbody.innerHTML = '';
            const users = data.users;

            users.forEach(user => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${user.name}</td>
                    <td>${user.email || ''}</td>
                `;
                const actionsCell = document.createElement('td');

                const deleteBtn = document.createElement('button');
                deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
                deleteBtn.classList.add('btn', 'btn-danger', 'btn-sm');
                deleteBtn.onclick = function() {
                    if (confirm(`Tem certeza que deseja excluir todas as ocupações de ${user.name}?`)) {
                        fetch(`/api/ocupacao/${user.id}`, {
                            method: 'DELETE',
                            headers: {
                                'Authorization': 'Bearer ' + localStorage.getItem('access_token')
                            }
                        }).then(response => {
                            if (response.ok) {
                                alert('Ocupações excluídas com sucesso!');
                                loadUsers();
                            } else {
                                alert('Falha ao excluir as ocupações.');
                            }
                        });
                    }
                };

                actionsCell.appendChild(deleteBtn);
                row.appendChild(actionsCell);
                tbody.appendChild(row);
            });
        });
}

document.addEventListener('DOMContentLoaded', () => {
    verificarAutenticacao();
    verificarPermissaoAdmin();
    window.gerenciadorInstrutores = new GerenciadorInstrutores();
    loadUsers();
});
