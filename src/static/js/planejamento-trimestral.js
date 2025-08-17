/* global bootstrap, showToast, chamarAPI, escapeHTML */

document.addEventListener('DOMContentLoaded', () => {
    // ---
    // Elementos do DOM (mantenha os existentes)
    // ---
    const btnAdicionar = document.getElementById('btn-adicionar-planejamento');
    const tabelaPlanejamento = document.getElementById('tabela-planejamento-trimestral').getElementsByTagName('tbody')[0];
    const modalEl = document.getElementById('modal-planejamento');
    const modal = new bootstrap.Modal(modalEl);
    const form = document.getElementById('form-planejamento');
    const contadorLinhasEl = document.getElementById('contador-linhas');

    // Cache para armazenar os dados da base de dados
    let cacheOpcoes = null;

    // -------------------
    // Funções
    // -------------------

    /**
     * Busca os dados para os selects da API.
     * Utiliza um cache para evitar buscas repetidas.
     * @returns {Promise<Object>} Um objeto com as listas de opções.
     */
    async function carregarOpcoesDaAPI() {
        if (cacheOpcoes) {
            return cacheOpcoes;
        }

        try {
            // Faz chamadas concorrentes para a API para buscar todas as opções
            const [dadosBase, treinamentos, instrutores] = await Promise.all([
                chamarAPI('/planejamento/basedados'),
                chamarAPI('/treinamentos/catalogo'),
                chamarAPI('/instrutores')
            ]);

            cacheOpcoes = {
                horario: dadosBase.horario || [],
                carga_horaria: dadosBase.carga_horaria || [],
                modalidade: dadosBase.modalidade || [],
                local: dadosBase.local || [],
                publico_alvo: dadosBase.publico_alvo || [],
                treinamento: treinamentos.map(t => t.nome) || [],
                instrutor: instrutores.map(i => i.nome) || []
            };
            
            return cacheOpcoes;
        } catch (error) {
            console.error('Erro ao carregar opções da API:', error);
            showToast('Erro ao carregar opções do formulário.', 'danger');
            return null;
        }
    }

    /**
     * Preenche um elemento <select> com uma lista de opções.
     * @param {HTMLSelectElement} selectEl - O elemento select a ser populado.
     * @param {string[]} opcoes - A lista de strings para as opções.
     * @param {string} placeholder - O texto inicial (ex: "Selecione...").
     */
    function popularSelect(selectEl, opcoes, placeholder) {
        if (!selectEl) return;
        selectEl.innerHTML = `<option value="">${placeholder}</option>`;
        opcoes.forEach((opcao) => {
            const optionEl = document.createElement('option');
            optionEl.value = opcao;
            optionEl.textContent = escapeHTML(opcao);
            selectEl.appendChild(optionEl);
        });
    }

    /**
     * Popula todos os selects do modal com os dados carregados da API.
     */
    async function popularFormulario() {
        const dados = await carregarOpcoesDaAPI();
        if (!dados) return;

        popularSelect(form.horario, dados.horario, 'Selecione um horário...');
        popularSelect(form.carga_horaria, dados.carga_horaria, 'Selecione uma C.H...');
        popularSelect(form.modalidade, dados.modalidade, 'Selecione uma modalidade...');
        popularSelect(form.treinamento, dados.treinamento, 'Selecione um treinamento...');
        popularSelect(form.instrutor, dados.instrutor, 'Selecione um instrutor...');
        popularSelect(form.local, dados.local, 'Selecione um local...');
        
        // Popula os campos de público alvo
        popularSelect(form.cmd, dados.publico_alvo, 'Nenhum');
        popularSelect(form.sjb, dados.publico_alvo, 'Nenhum');
        popularSelect(form.sag_tombos, dados.publico_alvo, 'Nenhum');
    }

    // --- Mantenha o restante das funções como estão ---
    // (atualizarContadorLinhas, validarFormulario, ordenarTabela, salvarPlanejamento, removerLinha)
    // ...

    /**
     * Calcula a diferença de dias entre duas datas e atualiza o contador de linhas.
     */
    function atualizarContadorLinhas() {
        const inicio = form.inicio.valueAsDate;
        const fim = form.fim.valueAsDate;

        if (inicio && fim && fim >= inicio) {
            const diffTime = Math.abs(fim - inicio);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
            contadorLinhasEl.textContent = `Serão criadas ${diffDays} linha(s) na tabela.`;
            contadorLinhasEl.classList.remove('d-none');
        } else {
            contadorLinhasEl.classList.add('d-none');
        }
    }

    /**
     * Valida o formulário antes de salvar.
     * @returns {boolean} True se o formulário for válido.
     */
    function validarFormulario() {
        let valido = true;
        form.querySelectorAll('[required]').forEach((input) => {
            if (!input.value) {
                input.classList.add('is-invalid');
                valido = false;
            } else {
                input.classList.remove('is-invalid');
            }
        });

        const inicio = form.inicio.valueAsDate;
        const fim = form.fim.valueAsDate;
        if (!inicio || !fim || fim < inicio) {
            form.fim.classList.add('is-invalid');
            valido = false;
        } else {
            form.fim.classList.remove('is-invalid');
        }

        if (!valido) {
            showToast('Por favor, corrija os campos marcados em vermelho.', 'warning');
        }

        return valido;
    }

    /**
     * Ordena as linhas da tabela pela coluna "Início" (data).
     */
    function ordenarTabela() {
        const rows = Array.from(tabelaPlanejamento.querySelectorAll('tr'));
        rows.sort((a, b) => {
            const dateA = a.dataset.date;
            const dateB = b.dataset.date;
            if (dateA < dateB) return -1;
            if (dateA > dateB) return 1;
            return 0;
        });
        rows.forEach((row) => tabelaPlanejamento.appendChild(row));
    }

    /**
     * Processa o envio do formulário: valida, cria e insere as linhas na tabela.
     * @param {Event} event - O evento de submit do formulário.
     */
    async function salvarPlanejamento(event) {
        event.preventDefault();
        if (!validarFormulario()) return;

        const dadosForm = Object.fromEntries(new FormData(form).entries());
        const dataInicio = new Date(`${dadosForm.inicio}T00:00:00-03:00`);
        const dataFim = new Date(`${dadosForm.fim}T00:00:00-03:00`);

        for (let d = new Date(dataInicio); d <= dataFim; d.setDate(d.getDate() + 1)) {
            const dataAtual = new Date(d);
            const dataFormatada = dataAtual.toISOString().split('T')[0];
            const diaSemana = dataAtual.toLocaleDateString('pt-BR', { weekday: 'long' });

            const newRow = tabelaPlanejamento.insertRow();
            newRow.dataset.date = dataFormatada;

            newRow.innerHTML = `
                <td>${dataFormatada.split('-').reverse().join('/')}</td>
                <td>${dataFormatada.split('-').reverse().join('/')}</td>
                <td>${diaSemana.charAt(0).toUpperCase() + diaSemana.slice(1)}</td>
                <td>${dadosForm.horario}</td>
                <td>${dadosForm.carga_horaria}</td>
                <td>${dadosForm.modalidade}</td>
                <td>${dadosForm.treinamento}</td>
                <td>${dadosForm.cmd || '-'}</td>
                <td>${dadosForm.sjb || '-'}</td>
                <td>${dadosForm.sag_tombos || '-'}</td>
                <td>${dadosForm.instrutor}</td>
                <td>${dadosForm.local}</td>
                <td>${dadosForm.observacao || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-danger btn-remover-linha">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
        }

        ordenarTabela();
        form.reset();
        contadorLinhasEl.classList.add('d-none');
        modal.hide();
        showToast('Planejamento adicionado com sucesso!', 'success');
    }

    /**
     * Remove uma linha da tabela.
     * @param {Event} event - O evento de clique no botão de remover.
     */
    function removerLinha(event) {
        if (event.target.closest('.btn-remover-linha')) {
            const row = event.target.closest('tr');
            row.remove();
            showToast('Linha removida.', 'info');
        }
    }


    // -------------------
    // Event Listeners
    // -------------------
    btnAdicionar.addEventListener('click', () => {
        if (!cacheOpcoes) {
            popularFormulario();
        }
        modal.show();
    });

    form.addEventListener('submit', salvarPlanejamento);
    tabelaPlanejamento.addEventListener('click', removerLinha);

    form.inicio.addEventListener('change', atualizarContadorLinhas);
    form.fim.addEventListener('change', atualizarContadorLinhas);
});
