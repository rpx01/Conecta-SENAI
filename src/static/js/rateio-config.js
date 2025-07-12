class RateioConfigApp {
    constructor() {
        this.tableBody = document.getElementById('configsTableBody');
        this.btnSalvar = document.getElementById('btnSalvarConfig');
        this.modal = new bootstrap.Modal(document.getElementById('configModal'));
        this.form = document.getElementById('configForm');
        this.registrarEventos();
        this.carregarConfigs();
    }

    registrarEventos() {
        this.btnSalvar.addEventListener('click', () => this.salvar());
    }

    async carregarConfigs() {
        try {
            const configs = await chamarAPI('/rateio-configs');
            this.tableBody.innerHTML = configs.map(c => `
                <tr data-id="${c.id}">
                    <td>${escapeHTML(c.filial)}</td>
                    <td>${escapeHTML(c.uo)}</td>
                    <td>${escapeHTML(c.cr)}</td>
                    <td>${escapeHTML(c.classe_valor)}</td>
                    <td><button class="btn btn-sm btn-danger btn-excluir" data-id="${c.id}"><i class="bi bi-trash"></i></button></td>
                </tr>`).join('');
            this.tableBody.querySelectorAll('.btn-excluir').forEach(btn => {
                btn.addEventListener('click', (e) => this.excluir(e.currentTarget.dataset.id));
            });
        } catch (e) {
            exibirAlerta(e.message, 'danger');
        }
    }

    async salvar() {
        const data = {
            filial: this.form.filial.value,
            uo: this.form.uo.value,
            cr: this.form.cr.value,
            classe_valor: this.form.classe_valor.value
        };
        try {
            await chamarAPI('/rateio-configs', 'POST', data);
            this.modal.hide();
            this.form.reset();
            await this.carregarConfigs();
            exibirAlerta('Configuração salva!', 'success');
        } catch (e) {
            exibirAlerta(e.message, 'danger');
        }
    }

    async excluir(id) {
        if (!confirm('Excluir esta configuração?')) return;
        try {
            await chamarAPI(`/rateio-configs/${id}`, 'DELETE');
            await this.carregarConfigs();
        } catch (e) {
            exibirAlerta(e.message, 'danger');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    verificarAutenticacao();
    verificarPermissaoAdmin();
    new RateioConfigApp();
});
