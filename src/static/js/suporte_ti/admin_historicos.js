/* global bootstrap, chamarAPI, verificarAutenticacao, verificarPermissaoAdmin, getUsuarioLogado, formatarData, sanitizeHTML */

(function () {
    const tabela = document.querySelector('#tabelaHistoricos tbody');
    const totalHistoricosEl = document.getElementById('totalHistoricos');
    const detalhesContainer = document.getElementById('detalhesHistorico');
    const listaAnexos = document.getElementById('listaAnexosHistorico');
    const modalEl = document.getElementById('modalDetalhesHistorico');
    const modal = modalEl ? new bootstrap.Modal(modalEl) : null;

    async function inicializar() {
        const autenticado = await verificarAutenticacao();
        if (!autenticado) return;
        const admin = await verificarPermissaoAdmin();
        if (!admin) return;
        atualizarNomeUsuario();
        await carregarHistoricos();
    }

    function atualizarNomeUsuario() {
        const usuario = getUsuarioLogado();
        if (usuario) {
            const span = document.getElementById('userName');
            if (span) {
                span.textContent = usuario.nome;
            }
        }
    }

    async function carregarHistoricos() {
        try {
            const chamados = await chamarAPI('/suporte_ti/admin/todos_chamados?status=Finalizado,Cancelado');
            renderizarChamados(chamados || []);
        } catch (error) {
            console.error(error);
            renderizarChamados([]);
        }
    }

    function renderizarChamados(chamados) {
        if (!tabela) return;
        tabela.innerHTML = '';
        const lista = Array.isArray(chamados) ? chamados : [];
        const total = lista.length;
        if (totalHistoricosEl) {
            totalHistoricosEl.textContent = `${total} registro${total === 1 ? '' : 's'}`;
        }
        if (!total) {
            const linha = document.createElement('tr');
            linha.innerHTML = '<td colspan="8" class="text-center text-muted py-4">Nenhum histórico encontrado no momento.</td>';
            tabela.appendChild(linha);
            return;
        }
        lista.forEach((chamado, indice) => {
            const tr = document.createElement('tr');
            const statusAtual = chamado.status || '-';
            tr.innerHTML = `
                <th scope="row">${indice + 1}</th>
                <td>${formatarData(chamado.created_at)}</td>
                <td>${sanitizeHTML(chamado.nome || chamado.email || '')}</td>
                <td>${sanitizeHTML(chamado.area || '')}</td>
                <td>${sanitizeHTML(chamado.tipo_equipamento_nome || '-')}</td>
                <td><span class="badge text-bg-${classeUrgencia(chamado.nivel_urgencia)}">${sanitizeHTML(chamado.nivel_urgencia || '-')}</span></td>
                <td><span class="badge text-bg-${classeStatus(statusAtual)}">${sanitizeHTML(statusAtual)}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" data-acao="detalhes" title="Ver detalhes">
                        <i class="bi bi-eye"></i>
                    </button>
                </td>
            `;
            const botaoDetalhes = tr.querySelector('button[data-acao="detalhes"]');
            botaoDetalhes?.addEventListener('click', () => abrirModalDetalhes(chamado));
            tabela.appendChild(tr);
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
            case 'aberto':
                return 'primary';
            case 'em atendimento':
                return 'warning';
            case 'finalizado':
                return 'success';
            case 'cancelado':
                return 'secondary';
            default:
                return 'secondary';
        }
    }

    function abrirModalDetalhes(chamado) {
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
            ['Status', chamado.status || '-']
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
