document.addEventListener('DOMContentLoaded', function() {
    const mesAnoElemento = document.getElementById('mes-ano-atual');
    const mesAnteriorBotao = document.getElementById('mes-ano-anterior');
    const mesSeguinteBotao = document.getElementById('mes-ano-seguinte');
    const corpoTabela = document.getElementById('corpo-tabela');
    const cabecalhoTabela = document.querySelector('#tabela-instrutores thead tr:last-child');

    let dataAtual = new Date();

    async function buscarDadosEPopulaTabela() {
        try {
            const [instrutores, ocupacoes] = await Promise.all([
                fetch('/api/ocupacao/instrutores').then(res => res.json()),
                fetch(`/api/planejamento/ocupacoes?ano=${dataAtual.getFullYear()}&mes=${dataAtual.getMonth() + 1}`).then(res => res.json())
            ]);

            populaCabecalho(instrutores);
            populaTabela(instrutores, ocupacoes);
            atualizaMesAno();
        } catch (error) {
            console.error('Erro ao buscar dados:', error);
        }
    }

    function populaCabecalho(instrutores) {
        // Limpa o cabeçalho existente, exceto as colunas fixas
        while (cabecalhoTabela.children.length > 3) {
            cabecalhoTabela.removeChild(cabecalhoTabela.lastChild);
        }

        instrutores.forEach(instrutor => {
            const th = document.createElement('th');
            th.textContent = instrutor.nome;
            cabecalhoTabela.appendChild(th);
        });
    }

    function populaTabela(instrutores, ocupacoes) {
        corpoTabela.innerHTML = '';
        const ano = dataAtual.getFullYear();
        const mes = dataAtual.getMonth();
        const diasNoMes = new Date(ano, mes + 1, 0).getDate();

        for (let dia = 1; dia <= diasNoMes; dia++) {
            const data = new Date(ano, mes, dia);
            const diaDaSemana = data.toLocaleDateString('pt-BR', { weekday: 'long' });

            // Cria uma linha para o turno da Manhã
            const linhaManha = document.createElement('tr');
            
            // Colunas de Dia e Semana com rowspan
            if (dia === 1) { // Só adiciona o rowspan na primeira linha do dia
                const celulaDia = document.createElement('td');
                celulaDia.textContent = data.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
                celulaDia.rowSpan = 2;
                linhaManha.appendChild(celulaDia);

                const celulaSemana = document.createElement('td');
                celulaSemana.textContent = diaDaSemana;
                celulaSemana.rowSpan = 2;
                linhaManha.appendChild(celulaSemana);
            }

            const celulaTurnoManha = document.createElement('td');
            celulaTurnoManha.textContent = 'Manhã';
            linhaManha.appendChild(celulaTurnoManha);
            
            // Cria uma linha para o turno da Tarde
            const linhaTarde = document.createElement('tr');
            const celulaTurnoTarde = document.createElement('td');
            celulaTurnoTarde.textContent = 'Tarde';
            linhaTarde.appendChild(celulaTurnoTarde);


            instrutores.forEach(instrutor => {
                // Adiciona células para Manhã
                const celulaManha = document.createElement('td');
                const ocupacaoManha = ocupacoes.find(o => 
                    o.instrutor_id === instrutor.id && 
                    new Date(o.data).getDate() === dia &&
                    o.turno === 'Manhã'
                );
                celulaManha.textContent = ocupacaoManha ? ocupacaoManha.ocupacao : '';
                linhaManha.appendChild(celulaManha);

                // Adiciona células para Tarde
                const celulaTarde = document.createElement('td');
                const ocupacaoTarde = ocupacoes.find(o => 
                    o.instrutor_id === instrutor.id && 
                    new Date(o.data).getDate() === dia &&
                    o.turno === 'Tarde'
                );
                celulaTarde.textContent = ocupacaoTarde ? ocupacaoTarde.ocupacao : '';
                linhaTarde.appendChild(celulaTarde);
            });
            
            corpoTabela.appendChild(linhaManha);
            corpoTabela.appendChild(linhaTarde);
        }
    }

    function atualizaMesAno() {
        const nomeDoMes = dataAtual.toLocaleDateString('pt-BR', { month: 'long' });
        const ano = dataAtual.getFullYear();
        mesAnoElemento.textContent = `${nomeDoMes.charAt(0).toUpperCase() + nomeDoMes.slice(1)} de ${ano}`;
    }

    mesAnteriorBotao.addEventListener('click', () => {
        dataAtual.setMonth(dataAtual.getMonth() - 1);
        buscarDadosEPopulaTabela();
    });

    mesSeguinteBotao.addEventListener('click', () => {
        dataAtual.setMonth(dataAtual.getMonth() + 1);
        buscarDadosEPopulaTabela();
    });

    buscarDadosEPopulaTabela();
});

