/* global bootstrap, chamarAPI, showToast, verificarPermissaoAdmin, sanitizeHTML */

document.addEventListener('DOMContentLoaded', async () => {
    const possuiPermissao = await verificarPermissaoAdmin();
    if (!possuiPermissao) {
        return;
    }

    const tabelaBody = document.getElementById('newsAdminTableBody');
    const paginacaoEl = document.getElementById('newsAdminPagination');
    const totalBadge = document.getElementById('newsAdminTotal');
    const searchForm = document.getElementById('newsAdminSearchForm');
    const resetButton = document.getElementById('newsAdminReset');
    const exportarButton = document.getElementById('btnExportarNoticias');
    const modalEl = document.getElementById('noticiaModal');
    const noticiaModal = new bootstrap.Modal(modalEl);
    const confirmacaoModal = new bootstrap.Modal(document.getElementById('confirmacaoExclusaoModal'));
    const form = document.getElementById('noticiaForm');
    const btnSalvar = document.getElementById('btnSalvarNoticia');

    const inputBusca = document.getElementById('newsAdminSearch');
    const selectStatus = document.getElementById('newsAdminStatus');
    const selectDestaque = document.getElementById('newsAdminDestaque');

    let paginaAtual = 1;
    const porPagina = 10;
    let noticiaParaExcluir = null;

    async function carregarNoticias(page = 1) {
        tabelaBody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4">
                    <div class="spinner-border text-primary" role="status" aria-hidden="true"></div>
                    <span class="visually-hidden">Carregando notícias</span>
                </td>
            </tr>`;
        const params = new URLSearchParams({
            page: page.toString(),
            per_page: porPagina.toString(),
            include_inativas: 'true'
        });
        const termo = inputBusca.value.trim();
        if (termo) {
            params.append('busca', termo);
        }
        const status = selectStatus.value;
        if (status === 'ativos') {
            params.append('ativo', 'true');
        } else if (status === 'inativos') {
            params.append('ativo', 'false');
        }
        const destaque = selectDestaque.value;
        if (destaque === 'destaque') {
            params.append('destaque', 'true');
        } else if (destaque === 'comum') {
            params.append('destaque', 'false');
        }
        try {
            const resposta = await chamarAPI(`/noticias?${params.toString()}`);
            const noticias = resposta.items || [];
            totalBadge.textContent = `${resposta.total || noticias.length} registros`;
            if (noticias.length === 0) {
                tabelaBody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">Nenhuma notícia encontrada.</td></tr>';
            } else {
                tabelaBody.innerHTML = noticias.map(criarLinhaNoticia).join('');
                tabelaBody.querySelectorAll('[data-acao="editar"]').forEach(botao => {
                    botao.addEventListener('click', () => {
                        const id = Number.parseInt(botao.dataset.id, 10);
                        abrirEdicao(id);
                    });
                });
                tabelaBody.querySelectorAll('[data-acao="excluir"]').forEach(botao => {
                    botao.addEventListener('click', () => {
                        noticiaParaExcluir = Number.parseInt(botao.dataset.id, 10);
                        confirmacaoModal.show();
                    });
                });
            }
            paginaAtual = resposta.page || page;
            renderizarPaginacao(resposta.pages || 1, paginaAtual);
        } catch (error) {
            console.error('Erro ao carregar notícias', error);
            tabelaBody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Erro ao carregar notícias.</td></tr>';
        }
    }

    function criarLinhaNoticia(noticia) {
        const destaqueBadge = noticia.destaque ? '<span class="badge bg-warning text-dark">Destaque</span>' : '<span class="badge bg-light text-dark">Comum</span>';
        const statusBadge = noticia.ativo ? '<span class="badge bg-success">Publicado</span>' : '<span class="badge bg-secondary">Rascunho</span>';
        const dataFormatada = formatarDataTabela(noticia.data_publicacao);
        return `
            <tr>
                <td class="fw-semibold">${escapeHTML(noticia.titulo)}</td>
                <td>${dataFormatada}</td>
                <td>${destaqueBadge}</td>
                <td>${statusBadge}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary me-2" data-acao="editar" data-id="${noticia.id}" aria-label="Editar notícia ${escapeHTML(noticia.titulo)}">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" data-acao="excluir" data-id="${noticia.id}" aria-label="Excluir notícia ${escapeHTML(noticia.titulo)}">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    }

    function renderizarPaginacao(totalPaginas, pagina) {
        paginacaoEl.innerHTML = '';
        if (totalPaginas <= 1) return;
        const criarItem = (label, targetPage, disabled = false, active = false) => `
            <li class="page-item ${disabled ? 'disabled' : ''} ${active ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${targetPage}">${label}</a>
            </li>
        `;
        paginacaoEl.insertAdjacentHTML('beforeend', criarItem('Anterior', pagina - 1, pagina <= 1));
        for (let i = 1; i <= totalPaginas; i++) {
            paginacaoEl.insertAdjacentHTML('beforeend', criarItem(i, i, false, i === pagina));
        }
        paginacaoEl.insertAdjacentHTML('beforeend', criarItem('Próxima', pagina + 1, pagina >= totalPaginas));
        paginacaoEl.querySelectorAll('a[data-page]').forEach(link => {
            link.addEventListener('click', event => {
                event.preventDefault();
                const alvo = Number.parseInt(link.dataset.page, 10);
                if (!Number.isNaN(alvo) && alvo >= 1 && alvo <= totalPaginas && alvo !== paginaAtual) {
                    paginaAtual = alvo;
                    carregarNoticias(paginaAtual);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
        });
    }

    async function abrirEdicao(id) {
        try {
            const noticia = await chamarAPI(`/noticias/${id}?include_inativas=true`);
            preencherFormulario(noticia);
            document.getElementById('noticiaModalLabel').textContent = 'Editar notícia';
            noticiaModal.show();
        } catch (error) {
            console.error('Erro ao buscar notícia', error);
            showToast('Não foi possível carregar os dados da notícia.', 'danger');
        }
    }

    function preencherFormulario(noticia) {
        document.getElementById('noticiaId').value = noticia.id;
        document.getElementById('noticiaTitulo').value = noticia.titulo || '';
        document.getElementById('noticiaResumo').value = noticia.resumo || '';
        document.getElementById('noticiaConteudo').value = noticia.conteudo || '';
        document.getElementById('noticiaAutor').value = noticia.autor || '';
        document.getElementById('noticiaImagemUrl').value = noticia.imagem_url || '';
        document.getElementById('noticiaDestaque').checked = Boolean(noticia.destaque);
        document.getElementById('noticiaAtivo').checked = Boolean(noticia.ativo);
        if (noticia.data_publicacao) {
            const data = new Date(noticia.data_publicacao);
            const local = new Date(data.getTime() - data.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
            document.getElementById('noticiaDataPublicacao').value = local;
        } else {
            document.getElementById('noticiaDataPublicacao').value = '';
        }
    }

    function limparFormulario() {
        form.reset();
        document.getElementById('noticiaId').value = '';
        document.getElementById('noticiaModalLabel').textContent = 'Nova notícia';
    }

    async function salvarNoticia() {
        const dados = new FormData(form);
        const payload = {
            titulo: dados.get('titulo')?.toString().trim(),
            resumo: dados.get('resumo')?.toString().trim(),
            conteudo: dados.get('conteudo')?.toString().trim(),
            autor: dados.get('autor')?.toString().trim() || null,
            imagem_url: dados.get('imagem_url')?.toString().trim() || null,
            destaque: form.querySelector('#noticiaDestaque').checked,
            ativo: form.querySelector('#noticiaAtivo').checked
        };
        const dataPublicacao = dados.get('dataPublicacao');
        if (dataPublicacao) {
            const data = new Date(dataPublicacao);
            payload.dataPublicacao = data.toISOString();
        }
        const noticiaId = document.getElementById('noticiaId').value;
        const metodo = noticiaId ? 'PUT' : 'POST';
        const endpoint = noticiaId ? `/noticias/${noticiaId}` : '/noticias';
        try {
            btnSalvar.disabled = true;
            await chamarAPI(endpoint, metodo, payload);
            showToast('Notícia salva com sucesso!', 'success');
            noticiaModal.hide();
            limparFormulario();
            carregarNoticias(paginaAtual);
        } catch (error) {
            console.error('Erro ao salvar notícia', error);
            const mensagem = error?.message || 'Não foi possível salvar a notícia.';
            showToast(mensagem, 'danger');
        } finally {
            btnSalvar.disabled = false;
        }
    }

    async function excluirNoticia() {
        if (!noticiaParaExcluir) return;
        try {
            await chamarAPI(`/noticias/${noticiaParaExcluir}`, 'DELETE');
            showToast('Notícia excluída com sucesso.', 'success');
            confirmacaoModal.hide();
            carregarNoticias(paginaAtual);
        } catch (error) {
            console.error('Erro ao excluir notícia', error);
            showToast('Não foi possível excluir a notícia.', 'danger');
        } finally {
            noticiaParaExcluir = null;
        }
    }

    async function exportarNoticias() {
        try {
            const resposta = await chamarAPI('/noticias?include_inativas=true&per_page=500');
            const itens = resposta.items || [];
            if (itens.length === 0) {
                showToast('Nenhuma notícia para exportar.', 'info');
                return;
            }
            const cabecalho = ['id', 'titulo', 'resumo', 'conteudo', 'autor', 'imagem_url', 'destaque', 'ativo', 'data_publicacao'];
            const linhas = [cabecalho.join(';')];
            itens.forEach(item => {
                const linha = [
                    item.id,
                    protegerCSV(item.titulo),
                    protegerCSV(item.resumo),
                    protegerCSV(stripHTML(item.conteudo)),
                    protegerCSV(item.autor || ''),
                    protegerCSV(item.imagem_url || ''),
                    item.destaque ? '1' : '0',
                    item.ativo ? '1' : '0',
                    item.data_publicacao || ''
                ];
                linhas.push(linha.join(';'));
            });
            const blob = new Blob([linhas.join('\n')], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'noticias.csv';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Erro ao exportar notícias', error);
            showToast('Falha ao exportar as notícias.', 'danger');
        }
    }

    function protegerCSV(texto = '') {
        const sanitized = texto.replaceAll('"', '""');
        return `"${sanitized}"`;
    }

    function stripHTML(conteudo = '') {
        const div = document.createElement('div');
        div.innerHTML = sanitizeHTML?.(conteudo) || conteudo;
        return div.textContent || '';
    }

    function formatarDataTabela(dataISO) {
        if (!dataISO) return '<span class="text-muted">Sem data</span>';
        try {
            const data = new Date(dataISO);
            return data.toLocaleString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
        } catch (error) {
            return '<span class="text-muted">Sem data</span>';
        }
    }

    function escapeHTML(texto = '') {
        const div = document.createElement('div');
        div.textContent = texto;
        return div.innerHTML;
    }

    modalEl.addEventListener('hidden.bs.modal', limparFormulario);
    btnSalvar.addEventListener('click', salvarNoticia);
    searchForm.addEventListener('submit', event => {
        event.preventDefault();
        paginaAtual = 1;
        carregarNoticias(paginaAtual);
    });
    resetButton.addEventListener('click', () => {
        inputBusca.value = '';
        selectStatus.value = 'todos';
        selectDestaque.value = 'todos';
        paginaAtual = 1;
        carregarNoticias(paginaAtual);
    });
    document.getElementById('btnConfirmarExclusao').addEventListener('click', excluirNoticia);
    exportarButton.addEventListener('click', exportarNoticias);

    carregarNoticias(paginaAtual);
});
