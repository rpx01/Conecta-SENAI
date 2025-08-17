document.addEventListener('DOMContentLoaded', () => {
    // --- DADOS DE EXEMPLO (MOCK) ---
    // Substitua isso por chamadas à sua API real.
    const mockData = {
        treinamento: [
            { id: 1, nome: 'Gerenciamento de Risco' },
            { id: 2, nome: 'ALFI Básico' },
            { id: 3, nome: 'Aperfeiçoamento Prof Seg Trafego Mina FM' }
        ],
        instrutor: [
            { id: 1, nome: 'ANNA LETICIA' },
            { id: 2, nome: 'CLEBER' },
            { id: 3, nome: 'DANIELLE' }
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

    // --- FUNÇÕES PRINCIPAIS ---

    /**
     * Renderiza os dados nas tabelas da página.
     * @param {string} type - O tipo de dado a ser renderizado (ex: 'treinamento').
     */
    function renderizarTabela(type) {
        const tbody = document.getElementById(`tabela-${type}`);
        if (!tbody) return;

        tbody.innerHTML = '';
        const dados = mockData[type] || [];

        if (dados.length === 0) {
            tbody.innerHTML = `<tr><td colspan="2" class="text-center text-muted">Nenhum item cadastrado.</td></tr>`;
            return;
        }

        dados.forEach(item => {
            const tr = document.createElement('tr');
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
    window.abrirModal = (type, id = null) => {
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
            const item = mockData[type].find(i => i.id === id);
            if (item) {
                document.getElementById('itemId').value = id;
                document.getElementById('itemName').value = item.nome;
            }
        } else {
            // Modo Adição
            modalLabel.textContent = `Adicionar Novo ${titulo}`;
        }
        
        geralModal.show();
    };

    /**
     * Simula o salvamento de um item (adição ou edição).
     */
    function salvarItem() {
        const id = document.getElementById('itemId').value;
        const type = document.getElementById('itemType').value;
        const name = document.getElementById('itemName').value;

        if (!name.trim()) {
            alert('O nome não pode estar vazio.');
            return;
        }

        // ***** PONTO DE INTEGRAÇÃO COM BACKEND (INÍCIO) *****
        // Aqui você faria a chamada à sua API.
        console.log('Salvando item:', { id, type, name });
        if (id) { // Edição
            const index = mockData[type].findIndex(i => i.id == id);
            if (index > -1) mockData[type][index].nome = name;
        } else { // Adição
            const newId = (mockData[type].length > 0) ? Math.max(...mockData[type].map(i => i.id)) + 1 : 1;
            mockData[type].push({ id: newId, nome: name });
        }
        // ***** PONTO DE INTEGRAÇÃO COM BACKEND (FIM) *****

        renderizarTabela(type);
        geralModal.hide();
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
     * Simula a exclusão de um item.
     */
    function excluirItem() {
        const { type, id } = itemParaExcluir;
        if (!type || !id) return;
        
        // ***** PONTO DE INTEGRAÇÃO COM BACKEND (INÍCIO) *****
        // Aqui você faria a chamada à sua API para deletar.
        console.log('Excluindo item:', { type, id });
        const index = mockData[type].findIndex(i => i.id === id);
        if (index > -1) {
            mockData[type].splice(index, 1);
        }
        // ***** PONTO DE INTEGRAÇÃO COM BACKEND (FIM) *****
        
        renderizarTabela(type);
        confirmacaoModal.hide();
        itemParaExcluir = { type: null, id: null };
    }


    // --- REGISTRO DE EVENTOS ---
    document.getElementById('btnSalvarGeral').addEventListener('click', salvarItem);
    document.getElementById('btnConfirmarExclusao').addEventListener('click', excluirItem);


    // --- CARGA INICIAL ---
    renderizarTabela('treinamento');
    renderizarTabela('instrutor');
    renderizarTabela('local');
    renderizarTabela('modalidade');
    renderizarTabela('horario');
    renderizarTabela('cargahoraria');
});

