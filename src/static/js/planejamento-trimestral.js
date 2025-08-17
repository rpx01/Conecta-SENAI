/* global bootstrap */

document.addEventListener('DOMContentLoaded', () => {
    // --- SELETORES DE ELEMENTOS ---
    const modalEl = document.getElementById('modalAdicionarTreinamento');
    const form = document.getElementById('form-treinamento');
    const btnSalvar = document.getElementById('btn-salvar-treinamento');
    const tabelaBody = document.getElementById('tabela-planejamento-body');

    // --- FUNÇÕES DE INICIALIZAÇÃO ---

    /**
     * Carrega as opções dos selects e checkboxes do modal.
     */
    function popularFormulario() {
        // Popula os selects
        popularSelect('select-treinamento', baseDeDados.treinamentos);
        popularSelect('select-horario', baseDeDados.horarios);
        popularSelect('select-carga-horaria', baseDeDados.cargaHoraria);
        popularSelect('select-modalidade', baseDeDados.modalidades);
        popularSelect('select-instrutor', baseDeDados.instrutores);
        popularSelect('select-local', baseDeDados.locais);

        // Popula os checkboxes
        const containerPublicoAlvo = document.getElementById('checkbox-publico-alvo');
        containerPublicoAlvo.innerHTML = ''; // Limpa antes de adicionar
        baseDeDados.publicoAlvo.forEach((alvo) => {
            containerPublicoAlvo.innerHTML += `
                <div class="form-check form-check-inline">
                    <input class="form-check-input" type="checkbox" id="check-${alvo.toLowerCase()}" value="${alvo}">
                    <label class="form-check-label" for="check-${alvo.toLowerCase()}">${alvo}</label>
                </div>
            `;
        });
    }

    /**
     * Função auxiliar para preencher um <select> com opções.
     * @param {string} selectId - O ID do elemento <select>.
     * @param {string[]} opcoes - Um array de strings com as opções.
     */
    function popularSelect(selectId, opcoes) {
        const select = document.getElementById(selectId);
        select.innerHTML = '<option value="">Selecione...</option>';
        opcoes.forEach((opcao) => {
            select.innerHTML += `<option value="${opcao}">${opcao}</option>`;
        });
    }


    // --- LÓGICA DE MANIPULAÇÃO DE DADOS ---

    /**
     * Processa o formulário e adiciona as linhas na tabela.
     */
    function adicionarTreinamento() {
        // 1. Coleta dos dados do formulário
        const dataInicioStr = document.getElementById('data-inicio').value;
        const dataTerminoStr = document.getElementById('data-termino').value;
        const treinamento = document.getElementById('select-treinamento').value;
        const horario = document.getElementById('select-horario').value;
        const cargaHoraria = document.getElementById('select-carga-horaria').value;
        const modalidade = document.getElementById('select-modalidade').value;
        const instrutor = document.getElementById('select-instrutor').value;
        const local = document.getElementById('select-local').value;
        const observacao = document.getElementById('observacao').value;

        // Coleta os públicos-alvo selecionados
        const publicosAlvoSelecionados = [];
        document.querySelectorAll('#checkbox-publico-alvo input:checked').forEach((input) => {
            publicosAlvoSelecionados.push(input.value);
        });

        // Validação simples
        if (!dataInicioStr || !dataTerminoStr || !treinamento) {
            alert('Por favor, preencha os campos obrigatórios: Datas e Treinamento.');
            return;
        }

        // 2. Lógica para criar uma linha por dia
        const diasDaSemana = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"];
        let dataAtual = new Date(`${dataInicioStr}T00:00:00-03:00`); // Adiciona fuso para evitar problemas
        const dataFim = new Date(`${dataTerminoStr}T00:00:00-03:00`);

        while (dataAtual <= dataFim) {
            const novaLinha = document.createElement('tr');

            // Formata as datas para o padrão brasileiro
            const inicioFormatado = new Date(`${dataInicioStr}T00:00:00-03:00`).toLocaleDateString('pt-BR');
            const terminoFormatado = dataFim.toLocaleDateString('pt-BR');
            const diaAtualFormatado = dataAtual.toLocaleDateString('pt-BR');

            novaLinha.innerHTML = `
                <td>${diaAtualFormatado}</td>
                <td>${terminoFormatado}</td>
                <td>${diasDaSemana[dataAtual.getDay()]}</td>
                <td>${horario}</td>
                <td>${cargaHoraria}</td>
                <td>${modalidade}</td>
                <td>${treinamento}</td>
                <td>${publicosAlvoSelecionados.includes("CMD") ? "X" : ""}</td>
                <td>${publicosAlvoSelecionados.includes("SJB") ? "X" : ""}</td>
                <td>${publicosAlvoSelecionados.includes("SAG/TOMBOS") ? "X" : ""}</td>
                <td>${instrutor}</td>
                <td>${local}</td>
                <td>${observacao}</td>
            `;
            tabelaBody.appendChild(novaLinha);

            // Incrementa para o próximo dia
            dataAtual.setDate(dataAtual.getDate() + 1);
        }

        // 3. Limpa o formulário e fecha o modal
        form.reset();
        bootstrap.Modal.getInstance(modalEl).hide();
    }


    // --- EVENT LISTENERS ---
    btnSalvar.addEventListener('click', adicionarTreinamento);

    // --- EXECUÇÃO INICIAL ---
    popularFormulario();
});
