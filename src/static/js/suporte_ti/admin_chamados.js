/* global bootstrap, chamarAPI, verificarAutenticacao, verificarPermissaoAdmin, getUsuarioLogado, formatarData, sanitizeHTML, showToast */

(function () {
    const tabelaChamadosAbertos = document.querySelector('#tabelaChamadosAbertos tbody');
    const tabelaChamadosEmAtendimento = document.querySelector('#tabelaChamadosEmAtendimento tbody');
    const totalChamadosAbertosEl = document.getElementById('totalChamados');
    const totalChamadosAtendimentoEl = document.getElementById('totalChamadosAtendimento');
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
    const modalDetalhesEl = document.getElementById('modalDetalhesChamadoAdmin');
    const modalDetalhes = modalDetalhesEl ? new bootstrap.Modal(modalDetalhesEl) : null;
    const modalFinalizarEl = document.getElementById('modalFinalizarChamado');
    const modalFinalizar = modalFinalizarEl ? new bootstrap.Modal(modalFinalizarEl) : null;
    const observacoesFinalizacaoEl = document.getElementById('observacoesFinalizacao');
    const btnConfirmarFinalizacao = document.getElementById('btnConfirmarFinalizacao');

    let chamadoSelecionadoParaFinalizar = null;
    let textoOriginalBotaoFinalizacao = '';

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
        } else {
            params.set('status', 'Aberto,Em Atendimento');
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
            : '/suporte_ti/admin/todos_chamados?status=Aberto,Em Atendimento';
        try {
            const chamados = await chamarAPI(endpoint);
            renderizarChamados(chamados || []);
        } catch (error) {
            console.error(error);
            renderizarChamados([]);
        }
    }

    function renderizarChamados(chamados) {
        const listaChamados = Array.isArray(chamados) ? chamados : [];
        const chamadosAbertos = listaChamados.filter((item) => (item.status || '').toLowerCase() === 'aberto');
        const chamadosEmAtendimento = listaChamados.filter((item) => (item.status || '').toLowerCase() === 'em atendimento');

        atualizarTabelaAbertos(chamadosAbertos);
        atualizarTabelaEmAtendimento(chamadosEmAtendimento);
    }

    function atualizarTabelaAbertos(chamados) {
        if (!tabelaChamadosAbertos) return;
        tabelaChamadosAbertos.innerHTML = '';
        const total = Array.isArray(chamados) ? chamados.length : 0;
        if (totalChamadosAbertosEl) {
            totalChamadosAbertosEl.textContent = `${total} registro${total === 1 ? '' : 's'}`;
        }
        if (!total) {
            const linha = document.createElement('tr');
            linha.innerHTML = '<td colspan="8" class="text-center text-muted py-4">Nenhum chamado em aberto no momento.</td>';
            tabelaChamadosAbertos.appendChild(linha);
            return;
        }
        chamados.forEach((chamado, indice) => {
            const tr = document.createElement('tr');
            const statusAtual = chamado.status || 'Aberto';
            tr.innerHTML = `
                <th scope="row">${indice + 1}</th>
                <td>${formatarData(chamado.created_at)}</td>
                <td>${sanitizeHTML(chamado.nome || chamado.email || '')}</td>
                <td>${sanitizeHTML(chamado.area || '')}</td>
                <td>${sanitizeHTML(chamado.tipo_equipamento_nome || '-')}</td>
                <td><span class="badge text-bg-${classeUrgencia(chamado.nivel_urgencia)}">${sanitizeHTML(chamado.nivel_urgencia || '-')}</span></td>
                <td><span class="badge text-bg-${classeStatus(statusAtual)}">${sanitizeHTML(statusAtual)}</span></td>
                <td>
                    <div class="d-flex flex-wrap gap-2">
                        <button class="btn btn-sm btn-outline-primary" data-acao="detalhes" title="Ver detalhes">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-success" data-acao="atender" title="Mover para atendimento">
                            <i class="bi bi-headset"></i> Atender chamado
                        </button>
                    </div>
                </td>
            `;
            const botaoDetalhes = tr.querySelector('button[data-acao="detalhes"]');
            botaoDetalhes?.addEventListener('click', () => abrirModal(chamado));

            const botaoAtender = tr.querySelector('button[data-acao="atender"]');
            botaoAtender?.addEventListener('click', async () => {
                botaoAtender.disabled = true;
                const sucesso = await atualizarStatusChamado(chamado.id, 'Em Atendimento');
                if (!sucesso) {
                    botaoAtender.disabled = false;
                }
            });

            tabelaChamadosAbertos.appendChild(tr);
        });
    }

    function atualizarTabelaEmAtendimento(chamados) {
        if (!tabelaChamadosEmAtendimento) return;
        tabelaChamadosEmAtendimento.innerHTML = '';
        const total = Array.isArray(chamados) ? chamados.length : 0;
        if (totalChamadosAtendimentoEl) {
            totalChamadosAtendimentoEl.textContent = `${total} registro${total === 1 ? '' : 's'}`;
        }
        if (!total) {
            const linha = document.createElement('tr');
            linha.innerHTML = '<td colspan="8" class="text-center text-muted py-4">Nenhum chamado em atendimento.</td>';
            tabelaChamadosEmAtendimento.appendChild(linha);
            return;
        }
        chamados.forEach((chamado, indice) => {
            const statusAtual = chamado.status || 'Em Atendimento';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <th scope="row">${indice + 1}</th>
                <td>${formatarData(chamado.created_at)}</td>
                <td>${sanitizeHTML(chamado.nome || chamado.email || '')}</td>
                <td>${sanitizeHTML(chamado.area || '')}</td>
                <td>${sanitizeHTML(chamado.tipo_equipamento_nome || '-')}</td>
                <td><span class="badge text-bg-${classeUrgencia(chamado.nivel_urgencia)}">${sanitizeHTML(chamado.nivel_urgencia || '-')}</span></td>
                <td><span class="badge text-bg-${classeStatus(statusAtual)}">${sanitizeHTML(statusAtual)}</span></td>
                <td>
                    <div class="d-flex flex-wrap gap-2">
                        <button class="btn btn-sm btn-outline-primary" data-acao="detalhes" title="Ver detalhes">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-success" data-acao="finalizar" title="Finalizar chamado">
                            <i class="bi bi-check2"></i> Finalizar
                        </button>
                        <button class="btn btn-sm btn-outline-danger" data-acao="cancelar" title="Cancelar chamado">
                            <i class="bi bi-x-circle"></i> Cancelar
                        </button>
                    </div>
                </td>
            `;
            const botaoDetalhes = tr.querySelector('button[data-acao="detalhes"]');
            botaoDetalhes?.addEventListener('click', () => abrirModal(chamado));

            const botaoFinalizar = tr.querySelector('button[data-acao="finalizar"]');
            botaoFinalizar?.addEventListener('click', () => abrirModalFinalizacao(chamado));

            const botaoCancelar = tr.querySelector('button[data-acao="cancelar"]');
            botaoCancelar?.addEventListener('click', async () => {
                if (!window.confirm('Tem certeza de que deseja cancelar este chamado?')) {
                    return;
                }
                botaoCancelar.disabled = true;
                const sucesso = await atualizarStatusChamado(chamado.id, 'Cancelado');
                if (!sucesso) {
                    botaoCancelar.disabled = false;
                }
            });

            tabelaChamadosEmAtendimento.appendChild(tr);
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

    async function atualizarStatusChamado(chamadoId, novoStatus, corpoAdicional = {}) {
        try {
            const resposta = await chamarAPI(
                `/suporte_ti/admin/chamados/${chamadoId}/status`,
                'PUT',
                { status: novoStatus, ...corpoAdicional }
            );
            showToast(resposta?.mensagem || 'Status atualizado com sucesso!', 'success');
            await buscarChamados();
            return true;
        } catch (error) {
            const mensagem = error?.message || 'Não foi possível atualizar o status do chamado.';
            showToast(mensagem, 'danger');
            return false;
        }
    }

    function abrirModal(chamado) {
        if (!modalDetalhes || !detalhesContainer) return;
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
            ['Observações', chamado.observacoes || '-']
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
        modalDetalhes.show();
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

    function abrirModalFinalizacao(chamado) {
        if (!modalFinalizar) return;
        chamadoSelecionadoParaFinalizar = chamado;
        textoOriginalBotaoFinalizacao = btnConfirmarFinalizacao?.innerHTML || '';
        if (observacoesFinalizacaoEl) {
            observacoesFinalizacaoEl.value = '';
        }
        modalFinalizar.show();
    }

    async function confirmarFinalizacao() {
        if (!chamadoSelecionadoParaFinalizar) {
            modalFinalizar?.hide();
            return;
        }
        if (!btnConfirmarFinalizacao) return;
        textoOriginalBotaoFinalizacao = textoOriginalBotaoFinalizacao || btnConfirmarFinalizacao.innerHTML;
        btnConfirmarFinalizacao.disabled = true;
        btnConfirmarFinalizacao.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Finalizando...';
        const possuiCampoObservacoes = Boolean(observacoesFinalizacaoEl);
        const observacoes = possuiCampoObservacoes
            ? observacoesFinalizacaoEl.value.trim()
            : '';
        const corpo = possuiCampoObservacoes ? { observacoes } : {};
        const sucesso = await atualizarStatusChamado(chamadoSelecionadoParaFinalizar.id, 'Finalizado', corpo);
        btnConfirmarFinalizacao.disabled = false;
        btnConfirmarFinalizacao.innerHTML = textoOriginalBotaoFinalizacao || '<i class="bi bi-check2-circle me-2"></i>Confirmar finalização';
        if (sucesso) {
            modalFinalizar?.hide();
            chamadoSelecionadoParaFinalizar = null;
            if (observacoesFinalizacaoEl) {
                observacoesFinalizacaoEl.value = '';
            }
        }
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

    if (btnConfirmarFinalizacao) {
        btnConfirmarFinalizacao.addEventListener('click', confirmarFinalizacao);
    }

    document.addEventListener('DOMContentLoaded', inicializar);
})();
