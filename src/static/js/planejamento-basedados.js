document.addEventListener('DOMContentLoaded', () => {

    // --- VARIÁVEIS GLOBAIS ---
    const geralModal = new bootstrap.Modal(document.getElementById('geralModal'));
    const instrutorModal = new bootstrap.Modal(document.getElementById('instrutorModal'));
    const confirmacaoModal = new bootstrap.Modal(document.getElementById('confirmacaoModal'));
    let itemParaExcluir = { type: null, id: null };
    let areasDeAtuacao = [];

    // ===================================================================
    // FORMULÁRIO PRINCIPAL - ADIÇÃO DE ITENS
    // ===================================================================
    const formBaseDados = document.getElementById('formBaseDados');
    if (formBaseDados) {
        const btnAdicionarItem = document.getElementById('btnAdicionarItem');
        const selectInstrutor = document.getElementById('selectInstrutor');
        const listaBaseDados = document.getElementById('listaBaseDados');

        (async () => {
            try {
                const instrutores = await chamarAPI('/instrutores');
                selectInstrutor.innerHTML = '<option value="">Selecione…</option>' +
                    instrutores.map(i => `<option value="${i.id}">${escapeHTML(i.nome)}</option>`).join('');
                btnAdicionarItem.disabled = false;
            } catch (e) {
                console.error('Falha ao carregar instrutores', e);
                btnAdicionarItem.disabled = true;
            }
        })();

        formBaseDados.addEventListener('submit', (e) => {
            e.preventDefault();
            executarAcaoComFeedback(btnAdicionarItem, async () => {
                const dados = Object.fromEntries(new FormData(formBaseDados).entries());
                const criado = await chamarAPI('/planejamento-basedados/itens', 'POST', dados);
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.textContent = `${escapeHTML(criado.descricao)} — instrutor #${escapeHTML(criado.instrutor_id)}`;
                listaBaseDados.prepend(li);
                formBaseDados.reset();
                selectInstrutor.value = '';
            });
        });
    }

    // ===================================================================
    // LÓGICA PARA TREINAMENTOS (AGORA COM API)
    // ===================================================================
    async function carregarTreinamentosDaAPI() {
        try {
            const tbody = document.getElementById('tabela-treinamento');
            tbody.innerHTML = '';

            if (treinamentos.length === 0) {
                tbody.innerHTML = `<tr><td colspan="2" class="text-center text-muted">Nenhum treinamento cadastrado.</td></tr>`;
                return;
            }

            treinamentos.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${escapeHTML(item.nome)}</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="abrirModal('treinamento', ${item.id})"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-outline-danger" onclick="confirmarExclusao('treinamento', ${item.id})"><i class="bi bi-trash"></i></button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } catch (error) {
            console.error('Falha ao carregar treinamentos:', error);
            showToast('Não foi possível carregar a lista de treinamentos.', 'danger');
        }
    }


    // ===================================================================
    // LÓGICA PARA INSTRUTORES (MODAL COMPLETO)
    // ===================================================================

    async function carregarAreasParaModal() {
        if (areasDeAtuacao.length > 0) return;
        try {
            areasDeAtuacao = await chamarAPI('/instrutores/areas-atuacao');
            const select = document.getElementById('instrutorArea');
            select.innerHTML = '<option value="">Selecione...</option>';
            areasDeAtuacao.forEach(area => {
                select.innerHTML += `<option value="${escapeHTML(area.valor)}">${escapeHTML(area.nome)}</option>`;
            });
        } catch (e) {
            console.error('Falha ao carregar áreas de atuação:', e);
            showToast('Não foi possível carregar as áreas de atuação.', 'danger');
        }
    }

    async function carregarInstrutoresDaAPI() {
        try {
            const instrutores = await chamarAPI('/instrutores');
            const tbody = document.getElementById('tabela-instrutor');
            tbody.innerHTML = '';

            if (instrutores.length === 0) {
                tbody.innerHTML = `<tr><td colspan="2" class="text-center text-muted">Nenhum instrutor cadastrado.</td></tr>`;
                return;
            }

            instrutores.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${escapeHTML(item.nome)}</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="abrirModalInstrutor(${item.id})"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-outline-danger" onclick="confirmarExclusao('instrutor', ${item.id})"><i class="bi bi-trash"></i></button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } catch (error) {
            console.error('Falha ao carregar instrutores:', error);
            showToast('Não foi possível carregar a lista de instrutores.', 'danger');
        }
    }

    window.abrirModalInstrutor = async (id = null) => {
        await carregarAreasParaModal();
        const form = document.getElementById('formInstrutor');
        form.reset();
        document.getElementById('instrutorModalLabel').textContent = id ? 'Editar Instrutor' : 'Novo Instrutor';
        document.getElementById('instrutorId').value = id || '';

        if (id) {
            try {
                const instrutor = await chamarAPI(`/instrutores/${id}`);
                document.getElementById('instrutorNome').value = instrutor.nome;
                document.getElementById('instrutorEmail').value = instrutor.email || '';
                document.getElementById('instrutorArea').value = instrutor.area_atuacao || '';
                document.getElementById('instrutorStatus').value = instrutor.status || 'ativo';
                document.getElementById('instrutorObservacoes').value = instrutor.observacoes || '';
                (instrutor.disponibilidade || []).forEach(d => {
                    const el = document.getElementById(`disp${d.charAt(0).toUpperCase() + d.slice(1)}`);
                    if (el) el.checked = true;
                });
            } catch (e) {
                showToast(`Erro ao carregar dados do instrutor: ${e.message}`, 'danger');
                return;
            }
        }
        instrutorModal.show();
    };

    async function salvarInstrutor() {
        const id = document.getElementById('instrutorId').value;
        const disponibilidade = [];
        if (document.getElementById('dispManha').checked) disponibilidade.push('manha');
        if (document.getElementById('dispTarde').checked) disponibilidade.push('tarde');
        if (document.getElementById('dispNoite').checked) disponibilidade.push('noite');

        const body = {
            nome: document.getElementById('instrutorNome').value,
            email: document.getElementById('instrutorEmail').value,
            area_atuacao: document.getElementById('instrutorArea').value,
            status: document.getElementById('instrutorStatus').value,
            observacoes: document.getElementById('instrutorObservacoes').value,
            disponibilidade
        };

        if (!body.nome || !body.email) {
            showToast('Nome e E-mail são obrigatórios.', 'warning');
            return;
        }

        try {
            const endpoint = id ? `/instrutores/${id}` : '/instrutores';
            const method = id ? 'PUT' : 'POST';
            await chamarAPI(endpoint, method, body);
            showToast(`Instrutor ${id ? 'atualizado' : 'adicionado'} com sucesso!`, 'success');
            instrutorModal.hide();
            carregarInstrutoresDaAPI();
        } catch (e) {
            showToast(`Erro ao salvar instrutor: ${e.message}`, 'danger');
        }
    }


    // ===================================================================
    // LÓGICA PARA ITENS GENÉRICOS (AGORA COM API)
    // ===================================================================

    async function renderizarTabelaGenerica(type) {
        const tbody = document.getElementById(`tabela-${type}`);
        if (!tbody) return;

        try {
            const dados = await chamarAPI(`/planejamento-basedados/${type}`);
            tbody.innerHTML = '';

            if (dados.length === 0) {
                tbody.innerHTML = `<tr><td colspan="2" class="text-center text-muted">Nenhum item cadastrado.</td></tr>`;
                return;
            }

            dados.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${escapeHTML(item.nome)}</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="abrirModal('${type}', ${item.id}, '${escapeHTML(item.nome)}')"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-outline-danger" onclick="confirmarExclusao('${type}', ${item.id})"><i class="bi bi-trash"></i></button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } catch (error) {
            console.error(`Falha ao carregar ${type}:`, error);
            showToast(`Não foi possível carregar a lista de ${type}.`, 'danger');
            tbody.innerHTML = `<tr><td colspan="2" class="text-center text-danger">Erro ao carregar dados.</td></tr>`;
        }
    }

    window.abrirModal = (type, id = null, nome = '') => {
        const form = document.getElementById('geralForm');
        form.reset();

        document.getElementById('itemType').value = type;
        const modalLabel = document.getElementById('geralModalLabel');

        const titulos = {
            treinamento: 'Treinamento', local: 'Local', modalidade: 'Modalidade',
            horario: 'Horário', cargahoraria: 'Carga Horária', 'publico-alvo': 'Público Alvo'
        };
        const titulo = titulos[type] || 'Item';

        if (id) {
            modalLabel.textContent = `Editar ${titulo}`;
            document.getElementById('itemId').value = id;
            document.getElementById('itemName').value = nome;
        } else {
            modalLabel.textContent = `Adicionar Novo ${titulo}`;
            document.getElementById('itemId').value = '';
        }

        geralModal.show();
    };

    async function salvarItem() {
        const id = document.getElementById('itemId').value;
        const type = document.getElementById('itemType').value;
        const name = document.getElementById('itemName').value;

        if (!name.trim()) {
            showToast('O nome não pode estar vazio.', 'warning');
            return;
        }

        const endpoint = id ? `/planejamento-basedados/${type}/${id}` : `/planejamento-basedados/${type}`;
        const method = id ? 'PUT' : 'POST';

        try {
            await chamarAPI(endpoint, method, { nome: name });
            showToast(`Item ${id ? 'atualizado' : 'adicionado'} com sucesso!`, 'success');
            renderizarTabelaGenerica(type);
            geralModal.hide();
        } catch (e) {
            showToast(`Erro ao salvar item: ${e.message}`, 'danger');
        }
    }

    window.confirmarExclusao = (type, id) => {
        itemParaExcluir = { type, id };
        confirmacaoModal.show();
    };

    async function excluirItem() {
        const { type, id } = itemParaExcluir;
        if (!type || !id) return;

        let endpoint;
        let callback;

        if (type === 'instrutor') {
            endpoint = `/instrutores/${id}`;
            callback = carregarInstrutoresDaAPI;
        } else if (type === 'treinamento') {
            console.warn('Exclusão de treinamento ainda não implementada com API');
            return;
        } else {
            endpoint = `/planejamento-basedados/${type}/${id}`;
            callback = () => renderizarTabelaGenerica(type);
        }

        try {
            await chamarAPI(endpoint, 'DELETE');
            showToast('Item excluído com sucesso!', 'success');
            if (callback) callback();
        } catch (error) {
            showToast(`Erro ao excluir: ${error.message}`, 'danger');
        }

        confirmacaoModal.hide();
        itemParaExcluir = { type: null, id: null };
    }

    // --- REGISTRO DE EVENTOS E CARGA INICIAL ---
    document.getElementById('btnSalvarGeral').addEventListener('click', salvarItem);
    document.getElementById('btnSalvarInstrutor').addEventListener('click', salvarInstrutor);
    document.getElementById('btnConfirmarExclusao').addEventListener('click', excluirItem);

    carregarTreinamentosDaAPI(); // Alterado para carregar da API
    carregarInstrutoresDaAPI();
    renderizarTabelaGenerica('local');
    renderizarTabelaGenerica('modalidade');
    renderizarTabelaGenerica('horario');
    renderizarTabelaGenerica('cargahoraria');
    renderizarTabelaGenerica('publico-alvo');
});

