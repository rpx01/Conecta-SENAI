/* global bootstrap, chamarAPI, verificarAutenticacao, verificarPermissaoAdmin, getUsuarioLogado, formatarData, sanitizeHTML, showToast */

(function () {
    const tabelaHistorico = document.querySelector('#tabelaHistoricoChamados tbody');
    const totalHistoricoEl = document.getElementById('totalChamadosHistorico');
    const modalEl = document.getElementById('modalDetalhesHistorico');
    const modal = modalEl ? new bootstrap.Modal(modalEl) : null;
    const detalhesContainer = document.getElementById('detalhesChamadoHistorico');
    const listaAnexos = document.getElementById('listaAnexosHistorico');

    const STATUS_FINALIZADO = 'Finalizado';
    const STATUS_FINALIZADO_LEGACY = 'Fechado';
    const STATUS_CANCELADO = 'Cancelado';

    async function inicializar() {
        const autenticado = await verificarAutenticacao();
        if (!autenticado) return;
        const admin = await verificarPermissaoAdmin();
        if (!admin) return;
        atualizarNomeUsuario();
        await buscarHistorico();
    }

    function atualizarNomeUsuario() {
        const usuario = getUsuarioLogado();
        if (!usuario) return;
        const span = document.getElementById('userName');
        if (span) {
            span.textContent = usuario.nome;
        }
    }

    async function buscarHistorico() {
        try {
            const statusConsulta = [STATUS_FINALIZADO, STATUS_CANCELADO, STATUS_FINALIZADO_LEGACY].join(',');
            const endpoint = `/suporte_ti/admin/todos_chamados?status=${statusConsulta}`;
            const chamados = await chamarAPI(endpoint);
            renderizarHistorico(chamados || []);
        } catch (error) {
            console.error(error);
            showToast('Não foi possível carregar o histórico de atendimentos.', 'danger');
            renderizarHistorico([]);
        }
    }

    function renderizarHistorico(chamados) {
        if (!tabelaHistorico) return;
        tabelaHistorico.innerHTML = '';
        const total = Array.isArray(chamados) ? chamados.length : 0;
        if (totalHistoricoEl) {
            totalHistoricoEl.textContent = `${total} registro${total === 1 ? '' : 's'}`;
        }
        if (!total) {
            const linha = document.createElement('tr');
            linha.innerHTML = '<td colspan="10" class="text-center text-muted py-4">Nenhum chamado finalizado ou cancelado foi encontrado.</td>';
            tabelaHistorico.appendChild(linha);
            return;
        }

        chamados.forEach((chamado, indice) => {
            const status = chamado.status || '';
            const observacoes = chamado.observacoes_atendimento || chamado.observacoes || '';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <th scope="row">${indice + 1}</th>
                <td>${formatarData(chamado.created_at)}</td>
                <td>${sanitizeHTML(chamado.nome || chamado.email || '')}</td>
                <td>${sanitizeHTML(chamado.area || '')}</td>
                <td>${sanitizeHTML(chamado.tipo_equipamento_nome || '-')}</td>
                <td><span class="badge text-bg-${classeUrgencia(chamado.nivel_urgencia)}">${sanitizeHTML(chamado.nivel_urgencia || '-')}</span></td>
                <td><span class="badge text-bg-${classeStatus(status)}">${sanitizeHTML(status || '-')}</span></td>
                <td>${sanitizeHTML(observacoes || '-')}</td>
                <td>${formatarData(chamado.updated_at)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" data-acao="detalhes" title="Ver detalhes">
                        <i class="bi bi-eye"></i>
                    </button>
                </td>
            `;
            tr.querySelector('button[data-acao="detalhes"]')?.addEventListener('click', () => abrirModal(chamado));
            tabelaHistorico.appendChild(tr);
        });
    }

    function classeUrgencia(urgencia) {
        switch ((urgencia || '').toLowerCase()) {
            case 'alto':
                return 'danger';
            case 'médio':
            case 'medio':
                return 'warning';
            default:
                return 'secondary';
        }
    }

    function classeStatus(status) {
        switch ((status || '').toLowerCase()) {
            case 'finalizado':
            case 'fechado':
                return 'success';
            case 'cancelado':
                return 'secondary';
            default:
                return 'primary';
        }
    }

    function abrirModal(chamado) {
        if (!modal || !detalhesContainer) return;
        detalhesContainer.innerHTML = '';
        const campos = [
            ['Protocolo', `#${chamado.id}`],
            ['Data de abertura', formatarData(chamado.created_at)],
            ['Usuário', chamado.nome || chamado.email || '-'],
            ['Área', chamado.area || '-'],
            ['Tipo de equipamento', chamado.tipo_equipamento_nome || '-'],
            ['Patrimônio', chamado.patrimonio || '-'],
            ['Número de série', chamado.numero_serie || '-'],
            ['Descrição', chamado.descricao_problema || '-'],
            ['Nível de urgência', chamado.nivel_urgencia || '-'],
            ['Status', chamado.status || '-'],
            ['Observações', chamado.observacoes_atendimento || chamado.observacoes || '-'],
            ['Data de fechamento', formatarData(chamado.updated_at)],
        ];
        campos.forEach(([label, valor]) => {
            const dt = document.createElement('dt');
            dt.className = 'col-sm-4 fw-semibold';
            dt.textContent = label;
            const dd = document.createElement('dd');
            dd.className = 'col-sm-8';
            dd.textContent = valor || '-';
            detalhesContainer.appendChild(dt);
            detalhesContainer.appendChild(dd);
        });
        renderizarAnexos(chamado.anexos || []);
        modal.show();
    }

    function renderizarAnexos(anexos) {
        if (!listaAnexos) return;
        listaAnexos.innerHTML = '';
        if (!anexos.length) {
            return;
        }
        const titulo = document.createElement('h3');
        titulo.className = 'h6 mt-3';
        titulo.textContent = 'Anexos';
        const lista = document.createElement('ul');
        lista.className = 'list-unstyled';
        anexos.forEach((caminho, index) => {
            const li = document.createElement('li');
            const link = document.createElement('a');
            link.href = caminho;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = `Arquivo ${index + 1}`;
            li.appendChild(link);
            lista.appendChild(li);
        });
        listaAnexos.appendChild(titulo);
        listaAnexos.appendChild(lista);
    }

    document.addEventListener('DOMContentLoaded', inicializar);
})();
