let ticketsAdminCache = [];
let modalDetalhesAdmin;

function preencherSelectsBasicos() {
    const filtroUrgencia = document.getElementById('filtroUrgencia');
    const filtroStatus = document.getElementById('filtroStatusAdmin');
    if (filtroUrgencia) {
        Object.entries(window.__suporteTI.URGENCIA_LABELS).forEach(([valor, rotulo]) => {
            const option = document.createElement('option');
            option.value = valor;
            option.textContent = rotulo;
            filtroUrgencia.appendChild(option);
        });
    }
    if (filtroStatus) {
        Object.entries(window.__suporteTI.STATUS_LABELS).forEach(([valor, rotulo]) => {
            const option = document.createElement('option');
            option.value = valor;
            option.textContent = rotulo;
            filtroStatus.appendChild(option);
        });
    }
}

async function carregarDadosAuxiliares() {
    try {
        const [areas, equipamentos] = await Promise.all([
            window.__suporteTI.carregarAreas({ incluirInativas: true }),
            window.__suporteTI.carregarEquipamentos({ incluirInativos: true })
        ]);
        window.__suporteTI.preencherSelect(document.getElementById('filtroArea'), areas, { incluirOpcaoPadrao: true });
        window.__suporteTI.preencherSelect(document.getElementById('filtroEquipamento'), equipamentos, { incluirOpcaoPadrao: true });
    } catch (erro) {
        console.error('Erro ao carregar dados auxiliares', erro);
        showToast('Não foi possível carregar áreas e equipamentos.', 'danger');
    }
}

function formatarData(isoString) {
    if (!isoString) return '-';
    const data = new Date(isoString);
    if (Number.isNaN(data.getTime())) return isoString;
    return data.toLocaleString('pt-BR', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

function criarOpcoesSelect(valores, selecionado) {
    return Object.entries(valores)
        .map(([valor, rotulo]) => `<option value="${valor}" ${valor === selecionado ? 'selected' : ''}>${rotulo}</option>`)
        .join('');
}

function renderizarTabelaAdmin(chamados) {
    const tbody = document.querySelector('#tabelaAdmin tbody');
    if (!tbody) return;
    if (!Array.isArray(chamados) || chamados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-muted">Nenhum chamado encontrado com os filtros selecionados.</td></tr>';
        return;
    }

    tbody.innerHTML = chamados.map(ticket => {
        const urgenciaBadge = window.__suporteTI.criarBadge({
            texto: window.__suporteTI.formatarUrgencia(ticket.urgencia),
            classe: window.__suporteTI.obterBadgeUrgencia(ticket.urgencia)
        });
        const statusBadge = window.__suporteTI.criarBadge({
            texto: window.__suporteTI.formatarStatus(ticket.status),
            classe: window.__suporteTI.obterBadgeStatus(ticket.status)
        });

        return `
            <tr data-ticket-id="${ticket.id}">
                <td>#${ticket.id}</td>
                <td>${escapeHTML(formatarData(ticket.criado_em))}</td>
                <td>${escapeHTML(ticket.nome)}<br><small class="text-muted">${escapeHTML(ticket.email)}</small></td>
                <td>${escapeHTML(ticket.area_nome || '-')}</td>
                <td>${escapeHTML(ticket.equipamento_nome || '-')}</td>
                <td>
                    ${urgenciaBadge}
                    <select class="form-select form-select-sm mt-2 urgencia-select" aria-label="Urgência">
                        ${criarOpcoesSelect(window.__suporteTI.URGENCIA_LABELS, ticket.urgencia)}
                    </select>
                </td>
                <td>
                    ${statusBadge}
                    <select class="form-select form-select-sm mt-2 status-select" aria-label="Status">
                        ${criarOpcoesSelect(window.__suporteTI.STATUS_LABELS, ticket.status)}
                    </select>
                </td>
                <td class="text-end table-actions">
                    <button class="btn btn-primary btn-sm" data-action="atualizar">
                        <i class="bi bi-save me-1"></i>Salvar
                    </button>
                    <button class="btn btn-outline-secondary btn-sm" data-action="detalhes">
                        <i class="bi bi-eye"></i>
                    </button>
                </td>
            </tr>`;
    }).join('');
}

async function carregarChamadosAdmin() {
    const params = new URLSearchParams();
    const filtros = {
        status: document.getElementById('filtroStatusAdmin')?.value || '',
        urgencia: document.getElementById('filtroUrgencia')?.value || '',
        area_id: document.getElementById('filtroArea')?.value || '',
        equipamento_id: document.getElementById('filtroEquipamento')?.value || '',
        ordenacao: document.getElementById('filtroOrdenacao')?.value || 'data'
    };

    Object.entries(filtros).forEach(([chave, valor]) => {
        if (valor) params.append(chave, valor);
    });

    params.append('per_page', '100');

    try {
        const resposta = await chamarAPI(`/support/tickets?${params.toString()}`);
        ticketsAdminCache = resposta?.items || [];
        renderizarTabelaAdmin(ticketsAdminCache);
    } catch (erro) {
        console.error('Erro ao carregar chamados administrativos', erro);
        showToast('Não foi possível carregar os chamados administrativos.', 'danger');
    }
}

function preencherModal(ticket) {
    document.getElementById('adminDetalheSolicitante').textContent = ticket.nome;
    document.getElementById('adminDetalheEmail').textContent = ticket.email;
    document.getElementById('adminDetalheArea').textContent = ticket.area_nome || '-';
    document.getElementById('adminDetalheEquipamento').textContent = ticket.equipamento_nome || '-';
    document.getElementById('adminDetalheUrgencia').innerHTML = window.__suporteTI.criarBadge({
        texto: window.__suporteTI.formatarUrgencia(ticket.urgencia),
        classe: window.__suporteTI.obterBadgeUrgencia(ticket.urgencia)
    });
    document.getElementById('adminDetalheStatus').innerHTML = window.__suporteTI.criarBadge({
        texto: window.__suporteTI.formatarStatus(ticket.status),
        classe: window.__suporteTI.obterBadgeStatus(ticket.status)
    });
    document.getElementById('adminDetalhePatrimonio').textContent = ticket.patrimonio || '-';
    document.getElementById('adminDetalheSerie').textContent = ticket.numero_serie || '-';
    document.getElementById('adminDetalheDescricao').textContent = ticket.descricao || '-';

    const lista = document.getElementById('adminDetalheAnexos');
    lista.innerHTML = '';
    if (ticket.anexos && ticket.anexos.length) {
        ticket.anexos.forEach(anexo => {
            const li = document.createElement('li');
            const link = document.createElement('a');
            link.href = anexo.url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = anexo.nome_arquivo;
            li.appendChild(link);
            lista.appendChild(li);
        });
    } else {
        lista.innerHTML = '<li class="text-muted">Nenhum anexo.</li>';
    }
}

async function atualizarChamado(row) {
    const ticketId = Number(row.dataset.ticketId);
    const status = row.querySelector('.status-select')?.value;
    const urgencia = row.querySelector('.urgencia-select')?.value;

    const botao = row.querySelector('button[data-action="atualizar"]');
    const payload = { status, urgencia };

    try {
        setBusy(botao, true);
        const ticketAtualizado = await chamarAPI(`/support/tickets/${ticketId}`, 'PATCH', payload);
        showToast(`Chamado #${ticketAtualizado.id} atualizado com sucesso.`, 'success');
        const indice = ticketsAdminCache.findIndex(item => item.id === ticketAtualizado.id);
        if (indice >= 0) {
            ticketsAdminCache[indice] = ticketAtualizado;
            renderizarTabelaAdmin(ticketsAdminCache);
        }
    } catch (erro) {
        console.error('Erro ao atualizar chamado', erro);
        showToast('Não foi possível atualizar o chamado.', 'danger');
    } finally {
        setBusy(botao, false);
    }
}

function configurarEventos() {
    document.getElementById('btnFiltrar')?.addEventListener('click', carregarChamadosAdmin);
    document.getElementById('btnLimparFiltros')?.addEventListener('click', () => {
        document.getElementById('filtroArea').value = '';
        document.getElementById('filtroEquipamento').value = '';
        document.getElementById('filtroUrgencia').value = '';
        document.getElementById('filtroStatusAdmin').value = '';
        document.getElementById('filtroOrdenacao').value = 'data';
        carregarChamadosAdmin();
    });

    document.querySelector('#tabelaAdmin tbody')?.addEventListener('click', evento => {
        const row = evento.target.closest('tr[data-ticket-id]');
        if (!row) return;
        const botao = evento.target.closest('button[data-action]');
        if (!botao) return;
        const acao = botao.dataset.action;
        const ticketId = Number(row.dataset.ticketId);
        const ticket = ticketsAdminCache.find(item => item.id === ticketId);
        if (acao === 'atualizar') {
            atualizarChamado(row);
        } else if (acao === 'detalhes' && ticket) {
            preencherModal(ticket);
            if (!modalDetalhesAdmin) {
                modalDetalhesAdmin = new bootstrap.Modal(document.getElementById('modalDetalhesAdmin'));
            }
            modalDetalhesAdmin.show();
        }
    });
}

(async function init() {
    if (!(await verificarPermissaoAdmin())) return;
    preencherSelectsBasicos();
    await carregarDadosAuxiliares();
    configurarEventos();
    await carregarChamadosAdmin();
})();
