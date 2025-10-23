/* global bootstrap, chamarAPI, verificarAutenticacao, verificarPermissaoAdmin, getUsuarioLogado, formatarData, sanitizeHTML */

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
            tr.innerHTML = `
                <th scope="row">${indice + 1}</th>
                <td>${formatarData(chamado.created_at)}</td>
                <td>${sanitizeHTML(chamado.nome || chamado.email || '')}</td>
                <td>${sanitizeHTML(chamado.area || '')}</td>
                <td>${sanitizeHTML(chamado.tipo_equipamento_nome || '-')}</td>
                <td><span class="badge text-bg-${classeUrgencia(chamado.nivel_urgencia)}">${sanitizeHTML(chamado.nivel_urgencia || '-')}</span></td>
                <td><span class="badge text-bg-${classeStatus(chamado.status)}">${sanitizeHTML(chamado.status || '-')}</span></td>
                <td><button class="btn btn-sm btn-outline-primary" data-id="${chamado.id}"><i class="bi bi-eye"></i></button></td>
            `;
            const botao = tr.querySelector('button');
            botao?.addEventListener('click', () => abrirModal(chamado));
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
