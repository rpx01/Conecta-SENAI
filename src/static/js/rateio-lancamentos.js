class LancamentosApp {
    constructor() {
        this.selectInstrutor = document.getElementById('selectInstrutor');
        this.selectAno = document.getElementById('selectAno');
        this.selectConfig = document.getElementById('selectConfig');
        this.inputPercentual = document.getElementById('inputPercentual');
        this.btnAdicionar = document.getElementById('btnAdicionarLancamento');
        this.btnSalvar = document.getElementById('btnSalvarLancamentos');
        this.mesesContainer = document.getElementById('mesesContainer');
        this.mesesTimeline = document.getElementById('mesesTimeline');
        this.areaLancamento = document.getElementById('areaLancamento');
        this.lancamentosContainer = document.getElementById('lancamentosContainer');
        this.tituloLancamento = document.getElementById('tituloLancamento');
        this.totalPercentual = document.getElementById('totalPercentual');
        this.mesAtual = null;
        this.anoAtual = new Date().getFullYear();
        this.registrarEventos();
        this.carregarInstrutores();
        this.preencherAnos();
        this.carregarConfigs();
    }

    registrarEventos() {
        this.selectAno.addEventListener('change', () => this.renderizarMeses());
        this.selectInstrutor.addEventListener('change', () => this.renderizarMeses());
        this.btnAdicionar.addEventListener('click', () => this.adicionarItem());
        this.btnSalvar.addEventListener('click', () => this.salvar());
    }

    async carregarInstrutores() {
        try {
            const instrutores = await chamarAPI('/instrutores');
            this.selectInstrutor.innerHTML = '<option value="">Selecione</option>' +
                instrutores.map(i => `<option value="${i.id}">${escapeHTML(i.nome)}</option>`).join('');
        } catch (e) {
            exibirAlerta(e.message, 'danger');
        }
    }

    preencherAnos() {
        const ano = new Date().getFullYear();
        let options = '';
        for (let a = ano - 1; a <= ano + 1; a++) {
            options += `<option value="${a}" ${a === ano ? 'selected' : ''}>${a}</option>`;
        }
        this.selectAno.innerHTML = options;
    }

    async carregarConfigs() {
        try {
            const configs = await chamarAPI('/rateio-configs');
            this.selectConfig.innerHTML = '<option value="">Selecione</option>' +
                configs.map(c => `<option value="${c.id}">${escapeHTML(c.descricao)}</option>`).join('');
        } catch (e) {
            exibirAlerta(e.message, 'danger');
        }
    }

    renderizarMeses() {
        const instrutorId = this.selectInstrutor.value;
        if (!instrutorId) return;
        this.mesesContainer.innerHTML = '';
        for (let m = 1; m <= 12; m++) {
            const btn = document.createElement('button');
            btn.className = 'btn btn-outline-secondary';
            btn.textContent = m.toString().padStart(2, '0');
            btn.addEventListener('click', () => this.carregarLancamentos(m));
            this.mesesContainer.appendChild(btn);
        }
        this.mesesTimeline.style.display = 'block';
    }

    async carregarLancamentos(mes) {
        this.mesAtual = mes;
        const instrutorId = this.selectInstrutor.value;
        const ano = parseInt(this.selectAno.value, 10);
        this.tituloLancamento.textContent = `Lançamentos para ${mes.toString().padStart(2, '0')}/${ano}`;
        try {
            const lancamentos = await chamarAPI(`/rateio/lancamentos?instrutor_id=${instrutorId}&ano=${ano}&mes=${mes}`);
            this.lancamentosContainer.innerHTML = '';
            lancamentos.forEach(l => this.criarLinha(l));
            this.atualizarTotal();
            this.areaLancamento.style.display = 'block';
        } catch (e) {
            exibirAlerta(e.message, 'danger');
        }
    }

    criarLinha(lancamento) {
        const div = document.createElement('div');
        div.className = 'input-group mb-2';
        div.dataset.id = lancamento.rateio_config_id;
        div.innerHTML = `
            <span class="input-group-text flex-grow-1">${escapeHTML(lancamento.rateio_config.descricao)}</span>
            <input type="number" class="form-control percentual" value="${lancamento.percentual}" min="0" max="100">
            <button class="btn btn-outline-danger btn-remover" type="button"><i class="bi bi-trash"></i></button>`;
        div.querySelector('.btn-remover').addEventListener('click', () => {
            div.remove();
            this.atualizarTotal();
        });
        div.querySelector('.percentual').addEventListener('input', () => this.atualizarTotal());
        this.lancamentosContainer.appendChild(div);
    }

    adicionarItem() {
        const configId = this.selectConfig.value;
        const percent = parseFloat(this.inputPercentual.value || '0');
        if (!configId || percent <= 0) return;
        const selected = this.selectConfig.selectedOptions[0].textContent;
        this.criarLinha({ rateio_config_id: configId, percentual: percent, rateio_config: { descricao: selected } });
        this.inputPercentual.value = '';
        this.atualizarTotal();
    }

    atualizarTotal() {
        const valores = Array.from(this.lancamentosContainer.querySelectorAll('.percentual')).map(i => parseFloat(i.value) || 0);
        const total = valores.reduce((a, b) => a + b, 0);
        this.totalPercentual.textContent = total.toFixed(2);
    }

    async salvar() {
        const instrutorId = this.selectInstrutor.value;
        const ano = parseInt(this.selectAno.value, 10);
        const mes = this.mesAtual;
        if (!instrutorId || !mes) return;
        const lancamentos = Array.from(this.lancamentosContainer.children).map(div => ({
            rateio_config_id: parseInt(div.dataset.id, 10),
            percentual: parseFloat(div.querySelector('.percentual').value || '0')
        }));
        try {
            await chamarAPI('/rateio/lancamentos', 'POST', { instrutor_id: parseInt(instrutorId, 10), ano, mes, lancamentos });
            exibirAlerta('Lançamentos salvos!', 'success');
        } catch (e) {
            exibirAlerta(e.message, 'danger');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    verificarAutenticacao();
    verificarPermissaoAdmin();
    new LancamentosApp();
});
