/* global bootstrap, chamarAPI, verificarAutenticacao, verificarPermissaoAdmin, getUsuarioLogado, formatarData, sanitizeHTML, showToast */

(function () {
    const tabelaAbertos = document.querySelector('#tabelaChamadosAdmin tbody');
    const tabelaAtendimento = document.querySelector('#tabelaChamadosAtendimento tbody');
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
    const modalCancelarEl = document.getElementById('modalCancelarChamado');
    const modalFinalizar = modalFinalizarEl ? new bootstrap.Modal(modalFinalizarEl) : null;
    const modalCancelar = modalCancelarEl ? new bootstrap.Modal(modalCancelarEl) : null;
    const observacoesFinalizacaoEl = document.getElementById('observacoesFinalizacao');
    const btnConfirmarFinalizacao = document.getElementById('btnConfirmarFinalizacao');
    const btnConfirmarCancelamento = document.getElementById('btnConfirmarCancelamento');

    const STATUS_ABERTO = 'Aberto';
    const STATUS_ATENDIMENTO = 'Em Atendimento';
    const STATUS_FINALIZADO = 'Finalizado';
    const STATUS_CANCELADO = 'Cancelado';

    let chamadoSelecionado = null;

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

    function obterFiltrosBase() {
        const filtros = {};
        if (filtroUrgencia?.value) {
            filtros.nivel_urgencia = filtroUrgencia.value;
        }
        if (filtroArea?.value) {
            filtros.area = filtroArea.value;
        }
        if (filtroTipo?.value) {
            filtros.tipo_equipamento_id = filtroTipo.value;
        }
        if (filtroDataInicio?.value) {
            filtros.data_inicio = filtroDataInicio.value;
        }
        if (filtroDataFim?.value) {
            filtros.data_fim = filtroDataFim.value;
        }
        return filtros;
    }

    function montarEndpoint(parametros = {}) {
        const params = new URLSearchParams();
        Object.entries(parametros).forEach(([chave, valor]) => {
            if (valor !== undefined && valor !== null && valor !== '') {
                params.set(chave, valor);
            }
        });
        return params.toString()
            ? `/suporte_ti/admin/todos_chamados?${params.toString()}`
            : '/suporte_ti/admin/todos_chamados';
    }

    async function buscarChamados() {
        const filtrosBase = obterFiltrosBase();
        const statusSelecionados = obterStatusSelecionados();
        const deveBuscarAbertos = !statusSelecionados.length || statusSelecionados.includes(STATUS_ABERTO);
        const deveBuscarAtendimento = !statusSelecionados.length || statusSelecionados.includes(STATUS_ATENDIMENTO);

        if (deveBuscarAbertos) {
            try {
                const endpointAbertos = montarEndpoint({ ...filtrosBase, status: STATUS_ABERTO });
                const chamadosAbertos = await chamarAPI(endpointAbertos);
                renderizarChamadosAbertos(chamadosAbertos || []);
            } catch (error) {
                console.error(error);
                renderizarChamadosAbertos([]);
            }
        } else {
            renderizarChamadosAbertos([]);
        }

        if (deveBuscarAtendimento) {
            try {
                const endpointAtendimento = montarEndpoint({ ...filtrosBase, status: STATUS_ATENDIMENTO });
                const chamadosAtendimento = await chamarAPI(endpointAtendimento);
                renderizarChamadosAtendimento(chamadosAtendimento || []);
            } catch (error) {
                console.error(error);
                renderizarChamadosAtendimento([]);
            }
        } else {
            renderizarChamadosAtendimento([]);
        }
    }

    function renderizarChamadosAbertos(chamados) {
        if (!tabelaAbertos) return;
        tabelaAbertos.innerHTML = '';
        const total = Array.isArray(chamados) ? chamados.length : 0;
        if (totalChamadosAbertosEl) {
            totalChamadosAbertosEl.textContent = `${total} registro${total === 1 ? '' : 's'}`;
        }
        if (!total) {
            tabelaAbertos.appendChild(criarLinhaVazia(8));
            return;
        }
        chamados.forEach((chamado, indice) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <th scope="row">${indice + 1}</th>
                <td>${formatarData(chamado.created_at)}</td>
                <td>${sanitizeHTML(chamado.nome || chamado.email || '')}</td>
                <td>${sanitizeHTML(chamado.area || '')}</td>
                <td>${sanitizeHTML(chamado.tipo_equipamento_nome || '-')}</td>
                <td><span class="badge text-bg-${classeUrgencia(chamado.nivel_urgencia)}">${sanitizeHTML(chamado.nivel_urgencia || '-')}</span></td>
                <td><span class="badge text-bg-${classeStatus(STATUS_ABERTO)}">${STATUS_ABERTO}</span></td>
                <td>
                    <div class="d-flex flex-wrap gap-2">
                        <button class="btn btn-sm btn-outline-primary" data-acao="detalhes" title="Ver detalhes">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-primary" data-acao="atender" title="Atender chamado">
                            Atender Chamado
                        </button>
                    </div>
                </td>
            `;
            adicionarEventosLinhaAbertos(tr, chamado);
            tabelaAbertos.appendChild(tr);
        });
    }

    function adicionarEventosLinhaAbertos(linha, chamado) {
        const botaoDetalhes = linha.querySelector('button[data-acao="detalhes"]');
        botaoDetalhes?.addEventListener('click', () => abrirModalDetalhes(chamado));

        const botaoAtender = linha.querySelector('button[data-acao="atender"]');
        botaoAtender?.addEventListener('click', () => atualizarStatusChamado(chamado.id, STATUS_ATENDIMENTO));
    }

    function renderizarChamadosAtendimento(chamados) {
        if (!tabelaAtendimento) return;
        tabelaAtendimento.innerHTML = '';
        const total = Array.isArray(chamados) ? chamados.length : 0;
        if (totalChamadosAtendimentoEl) {
            totalChamadosAtendimentoEl.textContent = `${total} registro${total === 1 ? '' : 's'}`;
        }
        if (!total) {
            tabelaAtendimento.appendChild(criarLinhaVazia(8));
            return;
        }
        chamados.forEach((chamado, indice) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <th scope="row">${indice + 1}</th>
                <td>${formatarData(chamado.created_at)}</td>
                <td>${sanitizeHTML(chamado.nome || chamado.email || '')}</td>
                <td>${sanitizeHTML(chamado.area || '')}</td>
                <td>${sanitizeHTML(chamado.tipo_equipamento_nome || '-')}</td>
                <td><span class="badge text-bg-${classeUrgencia(chamado.nivel_urgencia)}">${sanitizeHTML(chamado.nivel_urgencia || '-')}</span></td>
                <td><span class="badge text-bg-${classeStatus(STATUS_ATENDIMENTO)}">${STATUS_ATENDIMENTO}</span></td>
                <td>
                    <div class="d-flex flex-wrap gap-2">
                        <button class="btn btn-sm btn-outline-primary" data-acao="detalhes" title="Ver detalhes">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-success" data-acao="finalizar" title="Finalizar atendimento">
                            Finalizar
                        </button>
                        <button class="btn btn-sm btn-outline-danger" data-acao="cancelar" title="Cancelar atendimento">
                            Cancelar
                        </button>
                    </div>
                </td>
            `;
            adicionarEventosLinhaAtendimento(tr, chamado);
            tabelaAtendimento.appendChild(tr);
        });
    }

    function adicionarEventosLinhaAtendimento(linha, chamado) {
        linha.querySelector('button[data-acao="detalhes"]')?.addEventListener('click', () => abrirModalDetalhes(chamado));

        const btnFinalizar = linha.querySelector('button[data-acao="finalizar"]');
        btnFinalizar?.addEventListener('click', () => abrirModalFinalizar(chamado));

        const btnCancelar = linha.querySelector('button[data-acao="cancelar"]');
        btnCancelar?.addEventListener('click', () => abrirModalCancelar(chamado));
    }

    function criarLinhaVazia(colspan) {
        const linha = document.createElement('tr');
        linha.innerHTML = `<td colspan="${colspan}" class="text-center text-muted py-4">Nenhum chamado encontrado com os filtros selecionados.</td>`;
        return linha;
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

    async function atualizarStatusChamado(chamadoId, novoStatus, dadosExtras = {}) {
        if (!chamadoId || !novoStatus) return false;

        try {
            const resposta = await chamarAPI(
                `/suporte_ti/admin/chamados/${chamadoId}/status`,
                'PUT',
                { status: novoStatus, ...dadosExtras }
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

    function abrirModalDetalhes(chamado) {
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
        modalDetalhes.show();
    }

    function abrirModalFinalizar(chamado) {
        if (!modalFinalizar) return;
        chamadoSelecionado = chamado;
        if (observacoesFinalizacaoEl) {
            observacoesFinalizacaoEl.value = '';
        }
        modalFinalizar.show();
    }

    function abrirModalCancelar(chamado) {
        if (!modalCancelar) return;
        chamadoSelecionado = chamado;
        modalCancelar.show();
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

    if (btnConfirmarFinalizacao) {
        btnConfirmarFinalizacao.addEventListener('click', async () => {
            if (!chamadoSelecionado) return;
            const observacoes = observacoesFinalizacaoEl?.value.trim();
            if (!observacoes) {
                showToast('Informe as observações sobre o atendimento para finalizar o chamado.', 'warning');
                return;
            }
            const atualizado = await atualizarStatusChamado(chamadoSelecionado.id, STATUS_FINALIZADO, {
                observacoes,
            });
            if (atualizado) {
                modalFinalizar?.hide();
                chamadoSelecionado = null;
            }
        });
    }

    if (btnConfirmarCancelamento) {
        btnConfirmarCancelamento.addEventListener('click', async () => {
            if (!chamadoSelecionado) return;
            const atualizado = await atualizarStatusChamado(chamadoSelecionado.id, STATUS_CANCELADO);
            if (atualizado) {
                modalCancelar?.hide();
                chamadoSelecionado = null;
            }
        });
    }

    document.addEventListener('DOMContentLoaded', inicializar);
})();
