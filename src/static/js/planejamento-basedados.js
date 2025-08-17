document.addEventListener('DOMContentLoaded', () => {
    // --- DADOS DE EXEMPLO (MOCK) ---
    // Os dados dos instrutores agora virão da API.
    // Mantemos os outros dados de exemplo por enquanto.
    const mockData = {
        treinamento: [
            { id: 1, nome: 'Gerenciamento de Risco' },
            { id: 2, nome: 'ALFI Básico' },
            { id: 3, nome: 'Aperfeiçoamento Prof Seg Trafego Mina FM' }
        ],
        local: [
            { id: 1, nome: 'ONLINE/HOME OFFICE' },
            { id: 2, nome: 'CMD' },
            { id: 3, nome: 'TRANSMISSÃO ONLINE' }
        ],
        modalidade: [
            { id: 1, nome: 'Semipresencial' },
            { id: 2, nome: 'Presencial' },
            { id: 3, nome: 'Online' }
        ],
        horario: [
            { id: 1, nome: '08:00 - 12:00' },
            { id: 2, nome: '13:00 - 17:00' },
            { id: 3, nome: '18:00 - 22:00' }
        ],
        cargahoraria: [
            { id: 1, nome: '4 horas' },
            { id: 2, nome: '8 horas' },
            { id: 3, nome: '16 horas' }
        ]
    };

    // --- VARIÁVEIS GLOBAIS ---
    const geralModal = new bootstrap.Modal(document.getElementById('geralModal'));
    const confirmacaoModal = new bootstrap.Modal(document.getElementById('confirmacaoModal'));
    let itemParaExcluir = { type: null, id: null };

    // --- FUNÇÕES DE CARREGAMENTO DE DADOS ---

    /**
     * Carrega os instrutores da API e renderiza a tabela.
     */
    async function carregarInstrutoresDaAPI() {
        try {
            const instrutores = await chamarAPI('/instrutores');
            renderizarTabela('instrutor', instrutores);
        } catch (error) {
            console.error('Falha ao carregar instrutores:', error);
            showToast('Não foi possível carregar a lista de instrutores.', 'danger');
            const tbody = document.getElementById('tabela-instrutor');
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="2" class="text-center text-danger">Falha ao carregar dados.</td></tr>`;
            }
        }
    }

    // --- FUNÇÕES PRINCIPAIS ---

    /**
     * Renderiza os dados nas tabelas da página.
     * @param {string} type - O tipo de dado a ser renderizado (ex: 'treinamento').
     * @param {Array} dados - A lista de dados a ser renderizada.
     */
    function renderizarTabela(type, dados) {
        const tbody = document.getElementById(`tabela-${type}`);
        if (!tbody) return;

        tbody.innerHTML = '';

        if (dados.length === 0) {
            tbody.innerHTML = `<tr><td colspan="2" class="text-center text-muted">Nenhum item cadastrado.</td></tr>`;
            return;
        }

        dados.forEach(item => {
            const tr = document.createElement('tr');
            // O campo principal para instrutores da API é 'nome'.
            tr.innerHTML = `
                <td>${escapeHTML(item.nome)}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="abrirModal('${type}', ${item.id})"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-outline-danger" onclick="confirmarExclusao('${type}', ${item.id})"><i class="bi bi-trash"></i></button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    /**
     * Abre o modal para adicionar ou editar um item.
     * @param {string} type - O tipo de item.
     * @param {number|null} id - O ID do item para edição, ou null para adição.
     */
    window.abrirModal = async (type, id = null) => {
        const form = document.getElementById('geralForm');
        form.reset();

        document.getElementById('itemType').value = type;
        const modalLabel = document.getElementById('geralModalLabel');

        const titulos = {
            treinamento: 'Treinamento',
            instrutor: 'Instrutor',
            local: 'Local',
            modalidade: 'Modalidade',
            horario: 'Horário',
            cargahoraria: 'Carga Horária'
        };
        const titulo = titulos[type] || 'Item';

        if (id) {
            // Modo Edição
            modalLabel.textContent = `Editar ${titulo}`;
            document.getElementById('itemId').value = id;

            try {
                let item;
                if (type === 'instrutor') {
                    item = await chamarAPI(`/instrutores/${id}`);
                } else {
                    item = mockData[type].find(i => i.id === id);
                }

                if (item) {
                    document.getElementById('itemName').value = item.nome;
                }
            } catch (error) {
                showToast(`Erro ao carregar dados para edição: ${error.message}`, 'danger');
                return;
            }

        } else {
            // Modo Adição
            modalLabel.textContent = `Adicionar Novo ${titulo}`;
            document.getElementById('itemId').value = '';
        }

        geralModal.show();
    };

    /**
     * Salva um item (adição ou edição), agora com lógica para a API.
     */
    async function salvarItem() {
        const id = document.getElementById('itemId').value;
        const type = document.getElementById('itemType').value;
        const name = document.getElementById('itemName').value;

        if (!name.trim()) {
            alert('O nome não pode estar vazio.');
            return;
        }

        try {
            if (type === 'instrutor') {
                const endpoint = id ? `/instrutores/${id}` : '/instrutores';
                const method = id ? 'PUT' : 'POST';
                // A API espera um objeto com o campo 'nome'
                await chamarAPI(endpoint, method, { nome: name });
                showToast(`Instrutor ${id ? 'atualizado' : 'adicionado'} com sucesso!`, 'success');
                carregarInstrutoresDaAPI(); // Recarrega a lista da API
            } else {
                // Lógica antiga para os dados mockados
                if (id) { // Edição
                    const index = mockData[type].findIndex(i => i.id == id);
                    if (index > -1) mockData[type][index].nome = name;
                } else { // Adição
                    const newId = (mockData[type].length > 0) ? Math.max(...mockData[type].map(i => i.id)) + 1 : 1;
                    mockData[type].push({ id: newId, nome: name });
                }
                renderizarTabela(type, mockData[type]);
            }
            geralModal.hide();
        } catch (error) {
            showToast(`Erro ao salvar: ${error.message}`, 'danger');
        }
    }

    /**
     * Abre o modal de confirmação para excluir um item.
     * @param {string} type - O tipo de item.
     * @param {number} id - O ID do item.
     */
    window.confirmarExclusao = (type, id) => {
        itemParaExcluir = { type, id };
        confirmacaoModal.show();
    };

    /**
     * Exclui um item, agora com lógica para a API.
     */
    async function excluirItem() {
        const { type, id } = itemParaExcluir;
        if (!type || !id) return;

        try {
            if (type === 'instrutor') {
                await chamarAPI(`/instrutores/${id}`, 'DELETE');
                showToast('Instrutor excluído com sucesso!', 'success');
                carregarInstrutoresDaAPI(); // Recarrega a lista da API
            } else {
                // Lógica antiga para os dados mockados
                const index = mockData[type].findIndex(i => i.id === id);
                if (index > -1) {
                    mockData[type].splice(index, 1);
                }
                renderizarTabela(type, mockData[type]);
            }
            confirmacaoModal.hide();
        } catch(error) {
            showToast(`Erro ao excluir: ${error.message}`, 'danger');
        } finally {
            itemParaExcluir = { type: null, id: null };
        }
    }

    // --- REGISTRO DE EVENTOS ---
    document.getElementById('btnSalvarGeral').addEventListener('click', salvarItem);
    document.getElementById('btnConfirmarExclusao').addEventListener('click', excluirItem);


    // --- CARGA INICIAL ---
    // Carrega instrutores da API e os outros dados do mock.
    carregarInstrutoresDaAPI();
    renderizarTabela('treinamento', mockData.treinamento);
    renderizarTabela('local', mockData.local);
    renderizarTabela('modalidade', mockData.modalidade);
    renderizarTabela('horario', mockData.horario);
    renderizarTabela('cargahoraria', mockData.cargahoraria);
});
