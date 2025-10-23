/* global bootstrap, chamarAPI, verificarAutenticacao, verificarPermissaoAdmin, getUsuarioLogado, formatarData, sanitizeHTML, showToast */

(function () {
    const tabela = document.querySelector('#tabelaChamadosAdmin tbody');
    const totalChamadosEl = document.getElementById('totalChamados');
    const filtroStatus = document.getElementById('filtroStatus');
    const filtroUrgencia = document.getElementById('filtroUrgencia');
    const filtroArea = document.getElementById('filtroArea');
    const filtroTipo = document.getElementById('filtroTipoEquipamento');
    const filtroDataInicio = document.getElementById('filtroDataInicio');
    const filtroDataFim = document.getElementById('filtroDataFim');
    const btnAplicarFiltros = document.getElementById('btnAplicarFiltros');
    const btnLimparFiltros = document.getElementById('btnLimparFiltros');
    const detalhesContainer = document.getElementById('detalhesChamadoAdmin');
    const listaAnexos = document.getElementById('listaAnexosAdmin');
    const modalEl = document.getElementById('modalDetalhesChamadoAdmin');
    const modal = modalEl ? new bootstrap.Modal(modalEl) : null;

    const statusOpcoes = ['Aberto', 'Em Andamento', 'Fechado', 'Cancelado'];

    async function inicializar() {
        const autenticado = await verificarAutenticacao();
        if (!autenticado) return;
        const admin = await verificarPermissaoAdmin();
        if (!admin) return;
        atualizarNomeUsuario();
        await carregarBaseFiltros();
        await buscarChamados();
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

    async function carregarBaseFiltros() {
        try {
            const dados = await chamarAPI('/suporte_ti/basedados_formulario');
            preencherSelect(filtroArea, dados.areas || [], 'Todas', 'nome');
            preencherSelect(filtroTipo, dados.tipos_equipamento || [], 'Todos');
        } catch (error) {
            console.error(error);
        }
    }

    function preencherSelect(selectEl, itens, placeholder, valueKey = 'id', labelKey = 'nome') {
        if (!selectEl) return;
        selectEl.innerHTML = '';
        if (placeholder !== undefined) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = placeholder;
            selectEl.appendChild(option);
        }
        itens.forEach((item) => {
            const option = document.createElement('option');
            option.value = item[valueKey];
            option.textContent = item[labelKey];
            selectEl.appendChild(option);
        });
    }

    function obterStatusSelecionados() {
        if (!filtroStatus) return [];
        return Array.from(filtroStatus.selectedOptions).map((opt) => opt.value);
    }

    async function buscarChamados() {
        const params = new URLSearchParams();
        const status = obterStatusSelecionados();
        if (status.length) {
            params.set('status', status.join(','));
        }
        if (filtroUrgencia?.value) {
            params.set('nivel_urgencia', filtroUrgencia.value);
        }
        if (filtroArea?.value) {
            params.set('area', filtroArea.value);
        }
        if (filtroTipo?.value) {
            params.set('tipo_equipamento_id', filtroTipo.value);
        }
        if (filtroDataInicio?.value) {
            params.set('data_inicio', filtroDataInicio.value);
        }
        if (filtroDataFim?.value) {
            params.set('data_fim', filtroDataFim.value);
        }
        const endpoint = params.toString()
            ? `/suporte_ti/admin/todos_chamados?${params.toString()}`
            : '/suporte_ti/admin/todos_chamados';
        try {
            const chamados = await chamarAPI(endpoint);
            renderizarChamados(chamados || []);
        } catch (error) {
            console.error(error);
            renderizarChamados([]);
        }
    }

    function renderizarChamados(chamados) {
        if (!tabela) return;
        tabela.innerHTML = '';
        const total = Array.isArray(chamados) ? chamados.length : 0;
        if (totalChamadosEl) {
            totalChamadosEl.textContent = `${total} registro${total === 1 ? '' : 's'}`;
        }
        if (!total) {
            const linha = document.createElement('tr');
            linha.innerHTML = '<td colspan="8" class="text-center text-muted py-4">Nenhum chamado encontrado com os filtros selecionados.</td>';
            tabela.appendChild(linha);
            return;
        }
        chamados.forEach((chamado, indice) => {
            const tr = document.createElement('tr');
            const statusNormalizado = (chamado.status || '').toLowerCase();
            const statusAtual =
                statusOpcoes.find((status) => status.toLowerCase() === statusNormalizado) ||
                statusOpcoes[0];
            const statusOptionsHtml = statusOpcoes
                .map(
                    (opcao) =>
                        `<option value="${opcao}"${opcao === statusAtual ? ' selected' : ''}>${opcao}</option>`
                )
                .join('');
            tr.innerHTML = `
                <th scope="row">${indice + 1}</th>
                <td>${formatarData(chamado.created_at)}</td>
                <td>${sanitizeHTML(chamado.nome || chamado.email || '')}</td>
                <td>${sanitizeHTML(chamado.area || '')}</td>
                <td>${sanitizeHTML(chamado.tipo_equipamento_nome || '-')}</td>
                <td><span class="badge text-bg-${classeUrgencia(chamado.nivel_urgencia)}">${sanitizeHTML(chamado.nivel_urgencia || '-')}</span></td>
                <td>
                    <div class="d-flex flex-column gap-1">
                        <span class="badge status-badge text-bg-${classeStatus(statusAtual)}">${sanitizeHTML(statusAtual)}</span>
                        <select class="form-select form-select-sm status-select" data-id="${chamado.id}">
                            ${statusOptionsHtml}
                        </select>
                    </div>
                </td>
                <td>
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-outline-primary" data-acao="detalhes" data-id="${chamado.id}" title="Ver detalhes">
                            <i class="bi bi-eye"></i>
                        </button>
                    </div>
                </td>
            `;
            const botao = tr.querySelector('button[data-acao="detalhes"]');
            botao?.addEventListener('click', () => abrirModal(chamado));

            const selectStatus = tr.querySelector('.status-select');
            const badgeStatus = tr.querySelector('.status-badge');
            if (selectStatus) {
                selectStatus.dataset.originalValue = statusAtual;
                selectStatus.addEventListener('change', () =>
                    atualizarStatusChamado(chamado.id, selectStatus.value, selectStatus, badgeStatus)
                );
            }
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
            case 'em andamento':
                return 'warning';
            case 'fechado':
                return 'success';
            case 'cancelado':
                return 'secondary';
            default:
                return 'secondary';
        }
    }

    function atualizarClasseBadge(badgeEl, status) {
        if (!badgeEl) return;
        const classes = ['text-bg-primary', 'text-bg-warning', 'text-bg-success', 'text-bg-secondary'];
        badgeEl.classList.remove(...classes);
        badgeEl.classList.add(`text-bg-${classeStatus(status)}`);
        badgeEl.textContent = status || '-';
    }

    async function atualizarStatusChamado(chamadoId, novoStatus, selectEl, badgeEl) {
        if (!novoStatus) {
            showToast('Selecione um status válido para atualizar o chamado.', 'warning');
            selectEl.value = selectEl.dataset.originalValue || '';
            return;
        }
        if (novoStatus === selectEl.dataset.originalValue) {
            return;
        }

        selectEl.disabled = true;
        badgeEl?.classList.add('opacity-50');

        try {
            const resposta = await chamarAPI(
                `/suporte_ti/admin/chamados/${chamadoId}/status`,
                'PUT',
                { status: novoStatus }
            );
            selectEl.dataset.originalValue = novoStatus;
            atualizarClasseBadge(badgeEl, novoStatus);
            showToast(resposta?.mensagem || 'Status atualizado com sucesso!', 'success');
        } catch (error) {
            const mensagem = error?.message || 'Não foi possível atualizar o status do chamado.';
            showToast(mensagem, 'danger');
            selectEl.value = selectEl.dataset.originalValue || '';
        } finally {
            selectEl.disabled = false;
            badgeEl?.classList.remove('opacity-50');
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

    if (btnAplicarFiltros) {
        btnAplicarFiltros.addEventListener('click', buscarChamados);
    }

    if (btnLimparFiltros) {
        btnLimparFiltros.addEventListener('click', () => {
            filtroStatus && Array.from(filtroStatus.options).forEach((opt) => (opt.selected = false));
            if (filtroUrgencia) filtroUrgencia.value = '';
            if (filtroArea) filtroArea.value = '';
            if (filtroTipo) filtroTipo.value = '';
            if (filtroDataInicio) filtroDataInicio.value = '';
            if (filtroDataFim) filtroDataFim.value = '';
            buscarChamados();
        });
    }

    document.addEventListener('DOMContentLoaded', inicializar);
})();
