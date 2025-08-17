// src/static/js/planejamento-trimestral.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Verificações Iniciais ---
    if (!verificarAutenticacao()) {
        console.warn("Usuário não autenticado.");
        return;
    }
    const usuario = getUsuarioLogado();
    if (usuario) {
        document.getElementById('userName').textContent = usuario.nome;
    }

    // --- Dados (Mock e API) ---
    // Usamos os mesmos dados da página de base de dados para consistência.
    const mockData = {
        treinamento: [
            { id: 1, nome: 'NR 22 SEGURANCA E SAUDE OCUPACIONAL NA MINERACAO - AMBIENTACAO (2º Dia - AA e Contratada)&CONTRATADA' },
            { id: 2, nome: 'NR 22 SEGURANCA E SAUDE OCUPACIONAL NA MINERACAO - AMBIENTACAO (3º Dia - Filtragem)' },
        ],
        local: [
            { id: 1, nome: 'ONLINE/HOME OFFICE' },
            { id: 2, nome: 'CMD' },
            { id: 3, nome: 'TRANSMISSÃO ONLINE' },
            { id: 4, nome: 'SAG' }
        ],
        modalidade: [
            { id: 1, nome: 'Semipresencial' },
            { id: 2, nome: 'Presencial' },
            { id: 3, nome: 'Online' }
        ],
        horario: [
            { id: 1, nome: '08:00 às 16:00' },
            { id: 2, nome: '08:00 às 12:00' },
            { id: 3, nome: '18:00 - 22:00' }
        ],
        cargahoraria: [
            { id: 1, nome: '4 horas' },
            { id: 2, nome: '8 horas' },
            { id: 3, nome: '16 horas' },
            { id: 4, nome: '24 horas' }
        ],
        publicoalvo: [ // Nome ajustado para ser um identificador válido
            { id: 1, nome: 'PROJETOS' },
            { id: 2, nome: 'RECLEANER' },
            { id: 3, nome: 'Turma D' },
            { id: 4, nome: 'CMD' }
        ]
    };

    let instrutores = [];

    // --- Elementos do DOM ---
    const adicionarBtn = document.getElementById('adicionarTreinamentoBtn');
    const treinamentoModalEl = document.getElementById('treinamentoModal');
    const treinamentoModal = new bootstrap.Modal(treinamentoModalEl);
    const treinamentoForm = document.getElementById('treinamentoForm');
    const tabelaCorpo = document.getElementById('planejamentoTabelaCorpo');

    /**
     * Carrega dados dinâmicos (instrutores) da API.
     */
    async function carregarInstrutores() {
        if (instrutores.length > 0) return;
        try {
            instrutores = await chamarAPI('/instrutores');
        } catch (e) {
            console.error('Falha ao carregar instrutores:', e);
            showToast('Não foi possível carregar a lista de instrutores.', 'danger');
        }
    }

    /**
     * Preenche os seletores (dropdowns) do modal com os dados carregados.
     */
    function popularSeletoresModal() {
        const seletores = {
            'modalTreinamento': mockData.treinamento,
            'modalHorario': mockData.horario,
            'modalCargaHoraria': mockData.cargahoraria,
            'modalModalidade': mockData.modalidade,
            'modalCmd': mockData.publicoalvo,
            'modalSjb': mockData.publicoalvo,
            'modalSag': mockData.publicoalvo,
            'modalInstrutor': instrutores,
            'modalLocal': mockData.local,
        };

        for (const [id, data] of Object.entries(seletores)) {
            const select = document.getElementById(id);
            select.innerHTML = '<option value="">Selecione...</option>';
            data.forEach(item => {
                select.innerHTML += `<option value="${item.nome}">${escapeHTML(item.nome)}</option>`;
            });
        }
    }
    
    /**
     * Abre o modal de adição de treinamento.
     */
    adicionarBtn.addEventListener('click', async () => {
        treinamentoForm.reset();
        await carregarInstrutores();
        popularSeletoresModal();
        treinamentoModal.show();
    });

    /**
     * Lida com o envio do formulário do modal.
     */
    treinamentoForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const formData = new FormData(treinamentoForm);
        const dados = Object.fromEntries(formData.entries());

        const dataInicio = new Date(dados.inicio + 'T00:00:00-03:00');
        const dataTermino = new Date(dados.termino + 'T00:00:00-03:00');
        
        if (dataInicio > dataTermino) {
            showToast('A data de término não pode ser anterior à data de início.', 'warning');
            return;
        }

        // Gera as linhas da tabela para cada dia no intervalo
        let diaAtual = new Date(dataInicio);
        while (diaAtual <= dataTermino) {
            adicionarLinhaTabela(dados, new Date(diaAtual));
            diaAtual.setDate(diaAtual.getDate() + 1);
        }

        treinamentoModal.hide();
    });

    /**
     * Adiciona uma nova linha à tabela de planejamento.
     * @param {object} dados - Os dados do formulário.
     * @param {Date} dataLinha - A data específica para esta linha.
     */
    function adicionarLinhaTabela(dados, dataLinha) {
        const semana = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'][dataLinha.getDay()];
        
        // Formata a data no padrão dd/mm/aaaa
        const inicioFormatado = dataLinha.toLocaleDateString('pt-BR');
        const terminoFormatado = new Date(dados.termino + 'T00:00:00-03:00').toLocaleDateString('pt-BR');


        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${inicioFormatado}</td>
            <td>${terminoFormatado}</td>
            <td>${semana}</td>
            <td>${escapeHTML(dados.horario)}</td>
            <td>${escapeHTML(dados.ch)}</td>
            <td>${escapeHTML(dados.modalidade)}</td>
            <td>${escapeHTML(dados.treinamento)}</td>
            <td>${escapeHTML(dados.cmd)}</td>
            <td>${escapeHTML(dados.sjb)}</td>
            <td>${escapeHTML(dados.sag)}</td>
            <td>${escapeHTML(dados.instrutor)}</td>
            <td>${escapeHTML(dados.local)}</td>
            <td><input type="text" class="form-control form-control-sm" value="${escapeHTML(dados.observacao)}"></td>
        `;
        tabelaCorpo.appendChild(tr);
    }
});

