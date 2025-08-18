/* global bootstrap, showToast, chamarAPI, escapeHTML, executarAcaoComFeedback */

// Utilitários de conversão e validação
function toISODate(valor, campo = 'Data') {
    if (!valor) throw new Error(`${campo} obrigatória`);
    if (valor instanceof Date) {
        if (isNaN(valor)) throw new Error(`${campo} inválida`);
        return valor.toISOString().split('T')[0];
    }
    if (/^\d{4}-\d{2}-\d{2}$/.test(valor)) {
        return valor;
    }
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(valor)) {
        const [d, m, y] = valor.split('/');
        return `${y}-${m}-${d}`;
    }
    throw new Error(`${campo} inválida: ${valor}`);
}

function toHHMM(valor) {
    if (!/^\d{2}:\d{2}$/.test(valor)) {
        throw new Error(`Horário inválido: ${valor}`);
    }
    return valor;
}

function toNumber(valor, campo = 'Valor') {
    const num = Number(valor);
    if (Number.isNaN(num)) {
        throw new Error(`${campo} inválido`);
    }
    return num;
}

document.addEventListener('DOMContentLoaded', () => {
    const gerenciadorPlanejamento = {
        // --- SELETORES E ESTADO ---
        tabelaBody: document.getElementById('tabela-planejamento-trimestral').querySelector('tbody'),
        modalEl: document.getElementById('modal-planejamento'),
        form: document.getElementById('form-planejamento'),
        contadorLinhasEl: document.getElementById('contador-linhas'),
        confirmacaoModalEl: document.getElementById('confirmacaoExclusaoModal'),
        
        modal: null,
        confirmacaoModal: null,

        planejamentos: [], // Array em memória para armazenar os dados
        cacheOpcoes: null,
        loteParaExcluir: null,

        /**
         * Inicializa os componentes e os event listeners.
         */
        init() {
            this.modal = new bootstrap.Modal(this.modalEl);
            this.confirmacaoModal = new bootstrap.Modal(this.confirmacaoModalEl);

            document.getElementById('btn-adicionar-planejamento').addEventListener('click', () => this.abrirModal());
            this.form.addEventListener('submit', (e) => this.salvar(e));
            this.tabelaBody.addEventListener('click', (e) => this.handleTabelaClick(e));
            document.getElementById('btn-confirmar-exclusao').addEventListener('click', () => this.executarExclusao());

            this.form.inicio.addEventListener('change', () => this.atualizarContadorLinhas());
            this.form.fim.addEventListener('change', () => this.atualizarContadorLinhas());

            this.popularFormulario(); // Pré-carrega os selects
            this.carregarPlanejamentos();
        },

        // --- FUNÇÕES DE CARREGAMENTO E RENDERIZAÇÃO ---

        async carregarOpcoesDaAPI() {
            if (this.cacheOpcoes) return this.cacheOpcoes;
            try {
                const [dadosBase, treinamentosApi, instrutores] = await Promise.all([
                    chamarAPI('/planejamento/basedados'),
                    chamarAPI('/treinamentos/catalogo').catch(() => []),
                    chamarAPI('/instrutores')
                ]);

                let treinamentos = Array.isArray(treinamentosApi) && treinamentosApi.length
                    ? treinamentosApi.map(t => t.nome)
                    : [];

                if (!treinamentos.length) {
                    try {
                        const storage = JSON.parse(localStorage.getItem('planejamentoBaseDados'));
                        if (storage && Array.isArray(storage.treinamento)) {
                            treinamentos = storage.treinamento.map(t => t.nome);
                        }
                    } catch (e) {
                        console.error('Erro ao carregar treinamentos do localStorage:', e);
                    }
                }

                this.cacheOpcoes = {
                    horario: dadosBase.horario || [],
                    carga_horaria: dadosBase.carga_horaria || [],
                    modalidade: dadosBase.modalidade || [],
                    local: dadosBase.local || [],
                    publico_alvo: dadosBase.publico_alvo || [],
                    treinamentos,
                    instrutores: instrutores || []
                };
                return this.cacheOpcoes;
            } catch (error) {
                showToast('Erro ao carregar opções do formulário.', 'danger');
                return null;
            }
        },
        
        popularSelect(selectEl, opcoes, placeholder) {
            if (!selectEl) return;
            selectEl.innerHTML = `<option value="">${placeholder}</option>`;
            opcoes.forEach(opcao => {
                const optionEl = document.createElement('option');
                optionEl.value = opcao;
                optionEl.textContent = escapeHTML(opcao);
                selectEl.appendChild(optionEl);
            });
        },

        async popularFormulario() {
            const dados = await this.carregarOpcoesDaAPI();
            if (!dados) return;

            this.popularSelect(this.form.horario, dados.horario, 'Selecione...');
            this.popularSelect(this.form.carga_horaria, dados.carga_horaria, 'Selecione...');
            this.popularSelect(this.form.modalidade, dados.modalidade, 'Selecione...');
            this.popularSelect(this.form.treinamento, dados.treinamentos, 'Selecione...');
            this.popularSelect(this.form.instrutor, dados.instrutores.map(i => i.nome), 'Selecione...');
            this.popularSelect(this.form.local, dados.local, 'Selecione...');
            this.popularSelect(this.form.cmd, dados.publico_alvo, 'Nenhum');
            this.popularSelect(this.form.sjb, dados.publico_alvo, 'Nenhum');
            this.popularSelect(this.form.sag_tombos, dados.publico_alvo, 'Nenhum');
        },

        async carregarPlanejamentos() {
            try {
                const dados = await chamarAPI('/planejamento');
                this.planejamentos = Array.isArray(dados) ? dados : [];
                this.renderizarTabela();
            } catch (error) {
                showToast('Erro ao carregar planejamentos.', 'danger');
            }
        },

        renderizarTabela() {
            this.tabelaBody.innerHTML = '';
            this.planejamentos.sort((a, b) => new Date(a.data) - new Date(b.data));

            this.planejamentos.forEach(item => {
                const tr = document.createElement('tr');
                tr.dataset.rowId = item.rowId;
                tr.dataset.loteId = item.loteId;
                
                tr.innerHTML = `
                    <td>${this.formatarData(item.data)}</td>
                    <td>${this.formatarData(item.data)}</td>
                    <td>${item.semana}</td>
                    <td>${escapeHTML(item.horario)}</td>
                    <td>${escapeHTML(item.cargaHoraria)}</td>
                    <td>${escapeHTML(item.modalidade)}</td>
                    <td>${escapeHTML(item.treinamento)}</td>
                    <td>${escapeHTML(item.cmd || '-')}</td>
                    <td>${escapeHTML(item.sjb || '-')}</td>
                    <td>${escapeHTML(item.sagTombos || '-')}</td>
                    <td>${escapeHTML(item.instrutor)}</td>
                    <td>${escapeHTML(item.local)}</td>
                    <td>${escapeHTML(item.observacao || '-')}</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-outline-primary btn-editar-planejamento" title="Editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger btn-excluir-planejamento" title="Excluir Lote">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                `;
                this.tabelaBody.appendChild(tr);
            });
        },
        
        // --- LÓGICA DO MODAL E FORMULÁRIO ---

        abrirModal(modo = 'add', rowId = null) {
            this.form.reset();
            this.form.classList.remove('was-validated');
            this.contadorLinhasEl.classList.add('d-none');
            this.modalEl.dataset.mode = modo;
            this.modalEl.dataset.rowId = rowId || '';

            const label = this.modalEl.querySelector('#modalPlanejamentoLabel');
            const dataInicioInput = this.form.inicio;
            const dataFimInput = this.form.fim;

            if (modo === 'edit') {
                label.textContent = 'Editar Item do Planejamento';
                const item = this.planejamentos.find(p => p.rowId === rowId);
                if (item) {
                    // Preenche o formulário
                    Object.keys(item).forEach(key => {
                        if (this.form[key]) {
                            this.form[key].value = item[key];
                        }
                    });
                    // Ajusta nomes de campo
                    this.form.carga_horaria.value = item.cargaHoraria;
                    this.form.sag_tombos.value = item.sagTombos;
                    // Lida com as datas
                    dataInicioInput.value = item.data;
                    dataFimInput.value = item.data;
                    dataInicioInput.disabled = false; 
                    dataFimInput.disabled = true; // Em modo de edição, só pode alterar a data da linha
                }
            } else { // modo 'add'
                label.textContent = 'Adicionar Item ao Planejamento';
                dataInicioInput.disabled = false;
                dataFimInput.disabled = false;
            }

            this.modal.show();
        },

        async salvar(event) {
            event.preventDefault();
            if (!this.validarFormulario()) return;
            const btn = this.form.querySelector('button[type="submit"]');
            await executarAcaoComFeedback(btn, async () => {
                const modo = this.modalEl.dataset.mode;
                if (modo === 'edit') {
                    await this.executarEdicao();
                } else {
                    await this.executarAdicao();
                }
            });
        },

        async executarAdicao() {
            const dadosForm = Object.fromEntries(new FormData(this.form).entries());
            try {
                const dataInicio = new Date(`${dadosForm.inicio}T00:00:00`);
                const dataFim = new Date(`${dadosForm.fim}T00:00:00`);

                const linhas = [];
                for (let d = new Date(dataInicio); d <= dataFim; d.setDate(d.getDate() + 1)) {
                    const dia = new Date(d);
                    linhas.push({
                        inicio: toISODate(dia, 'Data inicial'),
                        fim: toISODate(dia, 'Data final'),
                        semana: this.getDiaSemana(dia),
                        horario: toHHMM(dadosForm.horario),
                        carga_horaria: parseInt(dadosForm.carga_horaria, 10),
                        modalidade: dadosForm.modalidade,
                        treinamento: dadosForm.treinamento,
                        polos: {
                            cmd: Boolean(dadosForm.cmd),
                            sjb: Boolean(dadosForm.sjb),
                            sag_tombos: Boolean(dadosForm.sag_tombos)
                        },
                        instrutor: dadosForm.instrutor,
                        local: dadosForm.local || '',
                        observacao: dadosForm.observacao || ''
                    });
                }

                const resp = await chamarAPI('/planejamento', 'POST', { registros: linhas });
                showToast(`Planejamento salvo (${resp.quantidade} linhas)`, 'success');
                await this.carregarPlanejamentos();
                this.finalizarAcao();
            } catch (error) {
                showToast(error.message, 'danger');
            }
        },

        async executarEdicao() {
            const rowId = this.modalEl.dataset.rowId;
            const itemIndex = this.planejamentos.findIndex(p => p.rowId === rowId);

            if (itemIndex > -1) {
                const dadosForm = Object.fromEntries(new FormData(this.form).entries());
                const dataAtualizada = new Date(`${dadosForm.inicio}T12:00:00Z`);

                // Atualiza os dados do objeto no array
                this.planejamentos[itemIndex] = {
                    ...this.planejamentos[itemIndex], // Mantém rowId e loteId
                    data: dataAtualizada.toISOString().split('T')[0],
                    semana: this.getDiaSemana(dataAtualizada),
                    horario: dadosForm.horario,
                    cargaHoraria: dadosForm.carga_horaria,
                    modalidade: dadosForm.modalidade,
                    treinamento: dadosForm.treinamento,
                    cmd: dadosForm.cmd,
                    sjb: dadosForm.sjb,
                    sagTombos: dadosForm.sag_tombos,
                    instrutor: dadosForm.instrutor,
                    local: dadosForm.local,
                    observacao: dadosForm.observacao
                };
                try {
                    await chamarAPI(`/planejamento/${rowId}`, 'PUT', this.planejamentos[itemIndex]);
                    showToast('Item atualizado com sucesso!', 'success');
                    this.finalizarAcao();
                } catch (error) {
                    showToast('Erro ao atualizar item.', 'danger');
                }
            } else {
                showToast('Erro: Item não encontrado para edição.', 'danger');
            }
        },
        
        finalizarAcao() {
            this.renderizarTabela();
            this.modal.hide();
        },

        // --- LÓGICA DE EXCLUSÃO ---
        
        confirmarExclusao(loteId) {
            this.loteParaExcluir = loteId;
            const linhasDoLote = this.planejamentos.filter(p => p.loteId === loteId).length;
            
            const modalBody = this.confirmacaoModalEl.querySelector('#confirmacaoExclusaoModalBody');
            modalBody.textContent = `Serão excluídas ${linhasDoLote} linha(s) deste lote. Deseja continuar?`;
            
            this.confirmacaoModal.show();
        },
        
        async executarExclusao() {
            if (this.loteParaExcluir) {
                try {
                    await chamarAPI(`/planejamento/lote/${this.loteParaExcluir}`, 'DELETE');
                    this.planejamentos = this.planejamentos.filter(p => p.loteId !== this.loteParaExcluir);
                    this.renderizarTabela();
                    showToast('Lote de planejamento excluído com sucesso!', 'info');
                } catch (error) {
                    showToast('Erro ao excluir lote.', 'danger');
                }
            }
            this.loteParaExcluir = null;
            this.confirmacaoModal.hide();
        },

        // --- MANIPULADORES DE EVENTOS E UTILITÁRIOS ---

        handleTabelaClick(event) {
            const btnEditar = event.target.closest('.btn-editar-planejamento');
            const btnExcluir = event.target.closest('.btn-excluir-planejamento');

            if (btnEditar) {
                const rowId = btnEditar.closest('tr').dataset.rowId;
                this.abrirModal('edit', rowId);
            }

            if (btnExcluir) {
                const loteId = btnExcluir.closest('tr').dataset.loteId;
                this.confirmarExclusao(loteId);
            }
        },

        atualizarContadorLinhas() {
            const inicio = this.form.inicio.valueAsDate;
            const fim = this.form.fim.valueAsDate;
            if (inicio && fim && fim >= inicio) {
                const diffTime = Math.abs(fim - inicio);
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
                this.contadorLinhasEl.textContent = `Serão criadas ${diffDays} linha(s) na tabela.`;
                this.contadorLinhasEl.classList.remove('d-none');
            } else {
                this.contadorLinhasEl.classList.add('d-none');
            }
        },
        
        validarFormulario() {
            this.form.classList.add('was-validated');
            return this.form.checkValidity();
        },

        getDiaSemana(data) {
            const dia = data.toLocaleDateString('pt-BR', { weekday: 'long' });
            return dia.charAt(0).toUpperCase() + dia.slice(1);
        },

        formatarData(dataISO) {
            const [ano, mes, dia] = dataISO.split('-');
            return `${dia}/${mes}/${ano}`;
        },
        
        gerarUUID() {
            return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
                (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
            );
        }
    };

    // Inicia a aplicação
    gerenciadorPlanejamento.init();
});

