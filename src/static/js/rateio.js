class RateioParametros {
    constructor() {
        this.tabelaBody = document.getElementById('tabelaParametros');
        const form = document.getElementById('formParametro');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.salvar();
        });
        this.carregar();
    }

    async carregar() {
        try {
            const lista = await chamarAPI('/rateio/parametros');
            this.tabelaBody.innerHTML = '';
            lista.forEach(p => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${escapeHTML(p.filial)}</td><td>${escapeHTML(p.uo)}</td><td>${escapeHTML(p.cr)}</td><td>${escapeHTML(p.classe_valor)}</td>`;
                this.tabelaBody.appendChild(tr);
            });
        } catch (e) {
            exibirAlerta('Erro ao carregar parâmetros', 'danger');
        }
    }

    async salvar() {
        const dados = {
            filial: document.getElementById('paramFilial').value,
            uo: document.getElementById('paramUo').value,
            cr: document.getElementById('paramCr').value,
            classe_valor: document.getElementById('paramClasse').value
        };
        try {
            await chamarAPI('/rateio/parametros', 'POST', dados);
            exibirAlerta('Parâmetro salvo', 'success');
            document.getElementById('formParametro').reset();
            this.carregar();
        } catch (e) {
            exibirAlerta(e.message, 'danger');
        }
    }
}

class RateioLancamentos {
    constructor() {
        this.instrutorSelect = document.getElementById('selectInstrutor');
        this.tabelaBody = document.getElementById('tabelaLancamentos');
        this.mesSelecionado = null;
        document.querySelectorAll('.mes-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.mesSelecionado = parseInt(btn.dataset.mes);
                this.carregar();
            });
        });
        document.getElementById('formLancamento').addEventListener('submit', (e) => {
            e.preventDefault();
            this.salvar();
        });
        this.carregarInstrutores();
    }

    async carregarInstrutores() {
        try {
            const insts = await chamarAPI('/instrutores');
            this.instrutorSelect.innerHTML = '<option value="">Selecione</option>';
            insts.forEach(i => {
                const opt = document.createElement('option');
                opt.value = i.id;
                opt.textContent = i.nome;
                this.instrutorSelect.appendChild(opt);
            });
        } catch {
            exibirAlerta('Erro ao carregar instrutores', 'danger');
        }
    }

    async carregar() {
        const instrutorId = this.instrutorSelect.value;
        if (!instrutorId || !this.mesSelecionado) return;
        const ano = new Date().getFullYear();
        try {
            const lancs = await chamarAPI(`/rateio/lancamentos?instrutor_id=${instrutorId}&mes=${this.mesSelecionado}&ano=${ano}`);
            this.tabelaBody.innerHTML = '';
            lancs.forEach(l => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${l.data_referencia}</td><td>${l.valor_total}</td><td>${l.horas_trabalhadas}</td><td>${escapeHTML(l.observacoes||'')}</td>`;
                this.tabelaBody.appendChild(tr);
            });
        } catch {
            exibirAlerta('Erro ao carregar lançamentos', 'danger');
        }
    }

    async salvar() {
        const instrutorId = this.instrutorSelect.value;
        if (!instrutorId || !this.mesSelecionado) return;
        const dados = {
            instrutor_id: parseInt(instrutorId),
            parametro_id: parseInt(document.getElementById('lancParametro').value),
            data_referencia: document.getElementById('lancData').value,
            valor_total: parseFloat(document.getElementById('lancValor').value),
            horas_trabalhadas: parseFloat(document.getElementById('lancHoras').value),
            observacoes: document.getElementById('lancObs').value
        };
        try {
            await chamarAPI('/rateio/lancamentos', 'POST', dados);
            exibirAlerta('Lançamento salvo', 'success');
            document.getElementById('formLancamento').reset();
            this.carregar();
        } catch (e) {
            exibirAlerta(e.message, 'danger');
        }
    }
}

window.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('formParametro')) {
        new RateioParametros();
    }
    if (document.getElementById('formLancamento')) {
        new RateioLancamentos();
    }
});
