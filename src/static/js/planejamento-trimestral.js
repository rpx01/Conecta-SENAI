document.addEventListener('DOMContentLoaded', () => {

    // --- DADOS DE EXEMPLO (MOCK) ---
    // Estes dados simulam o que viria da sua "Base de Dados"
    const baseDeDados = {
        treinamentos: [
            { id: 1, nome: 'NR 22 SEGURANCA E SAUDE OCUPACIONAL NA MINERACAO' },
            { id: 2, nome: 'NR23 Brigada de Emergencia' },
            { id: 3, nome: 'Bloqueio de Energia' }
        ],
        instrutores: [
            { id: 1, nome: 'IGOR' },
            { id: 2, nome: 'CLEBER' },
            { id: 3, nome: 'GUILHERME' }
        ],
        locais: [
            { id: 1, nome: 'TRANSMISSÃO ONLINE' },
            { id: 2, nome: 'CMD' },
            { id: 3, nome: 'SAG' }
        ],
        modalidades: [ { id: 1, nome: 'Online' }, { id: 2, nome: 'Presencial' } ],
        horarios: [ { id: 1, nome: '08:00 às 16:00' }, { id: 2, nome: '19:00 às 22:00' } ],
        cargasHorarias: [ { id: 1, nome: '24 horas' }, { id: 2, nome: '8 horas' }, { id: 3, nome: '4 horas' } ]
    };

    // --- DADOS DO PLANEJAMENTO (COMBINAÇÃO DOS DADOS ACIMA) ---
    // Criei um planejamento de exemplo para popular a tabela.
    const mockPlanejamento = [
        { inicio: '2025-07-01', termino: '2025-07-01', horario: '08:00 às 16:00', carga: '24 horas', modalidade: 'Online', treinamento: 'NR 22 SEGURANCA E SAUDE OCUPACIONAL NA MINERACAO', instrutor: 'IGOR', local: 'TRANSMISSÃO ONLINE' },
        { inicio: '2025-07-01', termino: '2025-07-01', horario: '08:00 às 12:00', carga: '4 horas', modalidade: 'Presencial', treinamento: 'NR23 Brigada de Emergencia', instrutor: 'CLEBER', local: 'CMD' },
        { inicio: '2025-04-10', termino: '2025-04-12', horario: '19:00 às 22:00', carga: '8 horas', modalidade: 'Presencial', treinamento: 'Bloqueio de Energia', instrutor: 'GUILHERME', local: 'SAG' },
        { inicio: '2025-01-20', termino: '2025-01-22', horario: '08:00 às 16:00', carga: '24 horas', modalidade: 'Online', treinamento: 'NR 22 SEGURANCA E SAUDE OCUPACIONAL NA MINERACAO', instrutor: 'IGOR', local: 'TRANSMISSÃO ONLINE' },
    ];

    const filtroAno = document.getElementById('filtro-ano');
    const filtroTrimestre = document.getElementById('filtro-trimestre');
    
    /**
     * Preenche os filtros de ano e trimestre com valores padrão.
     */
    function inicializarFiltros() {
        const anoAtual = new Date().getFullYear();
        for (let ano = anoAtual - 2; ano <= anoAtual + 2; ano++) {
            const option = new Option(ano, ano, ano === anoAtual, ano === anoAtual);
            filtroAno.add(option);
        }

        const mesAtual = new Date().getMonth(); // 0-11
        const trimestreAtual = Math.floor(mesAtual / 3) + 1;
        filtroTrimestre.value = trimestreAtual;

        filtroAno.addEventListener('change', renderizarTabela);
        filtroTrimestre.addEventListener('change', renderizarTabela);
    }

    /**
     * Renderiza a tabela de planejamento com base nos filtros selecionados.
     */
    function renderizarTabela() {
        const tbody = document.getElementById('corpo-tabela-planejamento');
        if (!tbody) return;

        const ano = parseInt(filtroAno.value);
        const trimestre = parseInt(filtroTrimestre.value);
        const [mesInicio, mesFim] = [ (trimestre - 1) * 3, trimestre * 3 ];

        const dadosFiltrados = mockPlanejamento.filter(item => {
            const dataItem = new Date(item.inicio + 'T00:00:00');
            const anoItem = dataItem.getFullYear();
            const mesItem = dataItem.getMonth();
            return anoItem === ano && mesItem >= mesInicio && mesItem < mesFim;
        });

        tbody.innerHTML = '';
        if (dadosFiltrados.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted">Nenhum treinamento planejado para este período.</td></tr>`;
            return;
        }

        dadosFiltrados.forEach(item => {
            const tr = document.createElement('tr');
            
            const diasDaSemana = ['Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado'];
            const dataInicio = new Date(item.inicio + 'T00:00:00');
            const diaSemana = diasDaSemana[dataInicio.getDay()];

            tr.innerHTML = `
                <td>${formatarData(item.inicio)}</td>
                <td>${formatarData(item.termino)}</td>
                <td>${diaSemana}</td>
                <td>${escapeHTML(item.horario)}</td>
                <td>${escapeHTML(item.carga)}</td>
                <td>${escapeHTML(item.modalidade)}</td>
                <td>${escapeHTML(item.treinamento)}</td>
                <td>${escapeHTML(item.instrutor)}</td>
                <td>${escapeHTML(item.local)}</td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    // --- FUNÇÕES DE UTILIDADE (Já devem existir no seu app.js, mas incluídas aqui para garantir) ---

    function escapeHTML(str) {
        if (str === null || str === undefined) return '';
        const div = document.createElement('div');
        div.textContent = String(str);
        return div.innerHTML;
    }

    function formatarData(dataISO) {
        if (!dataISO) return '';
        const [ano, mes, dia] = dataISO.split('-');
        return `${dia}/${mes}/${ano}`;
    }

    // --- INICIALIZAÇÃO ---
    inicializarFiltros();
    renderizarTabela();
});

