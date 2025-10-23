let ticketsCache = [];
let modalDetalhes;

function formatarData(isoString) {
    if (!isoString) return '-';
    const data = new Date(isoString);
    if (Number.isNaN(data.getTime())) return isoString;
    return data.toLocaleString('pt-BR', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

function preencherFiltroStatus() {
    const select = document.getElementById('filtroStatus');
    if (!select) return;
    Object.entries(window.__suporteTI.STATUS_LABELS).forEach(([valor, rotulo]) => {
        const option = document.createElement('option');
        option.value = valor;
        option.textContent = rotulo;
        select.appendChild(option);
    });
}

function renderizarTabela(chamados) {
    const tbody = document.querySelector('#tabelaChamados tbody');
    if (!tbody) return;
    if (!Array.isArray(chamados) || chamados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted">Nenhum chamado encontrado.</td></tr>';
        return;
    }

    const linhas = chamados.map(ticket => {
        const urgenciaBadge = window.__suporteTI.criarBadge({
            texto: window.__suporteTI.formatarUrgencia(ticket.urgencia),
            classe: window.__suporteTI.obterBadgeUrgencia(ticket.urgencia)
        });
        const statusBadge = window.__suporteTI.criarBadge({
            texto: window.__suporteTI.formatarStatus(ticket.status),
            classe: window.__suporteTI.obterBadgeStatus(ticket.status)
        });
        const descricao = escapeHTML(ticket.descricao || '').slice(0, 140);
        return `
            <tr>
                <td>#${ticket.id}</td>
                <td>${escapeHTML(formatarData(ticket.criado_em))}</td>
                <td>${escapeHTML(ticket.area_nome || '-')}</td>
                <td>${escapeHTML(ticket.equipamento_nome || '-')}</td>
                <td>${urgenciaBadge}</td>
                <td>${statusBadge}</td>
                <td class="ticket-description" title="${escapeHTML(ticket.descricao || '')}">${descricao}${ticket.descricao && ticket.descricao.length > 140 ? '...' : ''}</td>
                <td class="text-end">
                    <button class="btn btn-outline-primary btn-sm" data-action="detalhes" data-ticket-id="${ticket.id}">
                        <i class="bi bi-search"></i> Detalhes
                    </button>
                </td>
            </tr>`;
    }).join('');
    tbody.innerHTML = linhas;
}

function preencherModal(ticket) {
    if (!ticket) return;
    document.getElementById('detalheSolicitante').textContent = `${ticket.nome} (${ticket.email})`;
    document.getElementById('detalheArea').textContent = ticket.area_nome || '-';
    document.getElementById('detalheEquipamento').textContent = ticket.equipamento_nome || '-';
    document.getElementById('detalheUrgencia').innerHTML = window.__suporteTI.criarBadge({
        texto: window.__suporteTI.formatarUrgencia(ticket.urgencia),
        classe: window.__suporteTI.obterBadgeUrgencia(ticket.urgencia)
    });
    document.getElementById('detalheStatus').innerHTML = window.__suporteTI.criarBadge({
        texto: window.__suporteTI.formatarStatus(ticket.status),
        classe: window.__suporteTI.obterBadgeStatus(ticket.status)
    });
    document.getElementById('detalhePatrimonio').textContent = ticket.patrimonio || '-';
    document.getElementById('detalheSerie').textContent = ticket.numero_serie || '-';
    document.getElementById('detalheDescricao').textContent = ticket.descricao || '-';

    const listaAnexos = document.getElementById('detalheAnexos');
    listaAnexos.innerHTML = '';
    if (ticket.anexos && ticket.anexos.length) {
        ticket.anexos.forEach(anexo => {
            const li = document.createElement('li');
            const link = document.createElement('a');
            link.href = anexo.url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = anexo.nome_arquivo;
            li.appendChild(link);
            listaAnexos.appendChild(li);
        });
    } else {
        listaAnexos.innerHTML = '<li class="text-muted">Nenhum anexo enviado.</li>';
    }
}

async function carregarChamados() {
    const filtroStatus = document.getElementById('filtroStatus');
    const status = filtroStatus?.value || '';
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    try {
        const resposta = await chamarAPI(`/support/tickets/mine${query}`);
        ticketsCache = resposta || [];
        renderizarTabela(ticketsCache);
    } catch (erro) {
        console.error('Erro ao listar chamados', erro);
        showToast('Não foi possível carregar seus chamados.', 'danger');
    }
}

function configurarEventos() {
    document.getElementById('btnRecarregar')?.addEventListener('click', carregarChamados);
    document.getElementById('filtroStatus')?.addEventListener('change', carregarChamados);

    const tbody = document.querySelector('#tabelaChamados tbody');
    tbody?.addEventListener('click', evento => {
        const botao = evento.target.closest('button[data-action="detalhes"]');
        if (!botao) return;
        const ticketId = Number(botao.dataset.ticketId);
        const ticket = ticketsCache.find(item => item.id === ticketId);
        if (ticket) {
            preencherModal(ticket);
            if (!modalDetalhes) {
                modalDetalhes = new bootstrap.Modal(document.getElementById('modalDetalhes'));
            }
            modalDetalhes.show();
        }
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    if (!(await verificarAutenticacao())) return;
    preencherFiltroStatus();
    configurarEventos();
    await carregarChamados();
});
