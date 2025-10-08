/* global chamarAPI, showToast, getUsuarioLogado, sanitizeHTML */

document.addEventListener('DOMContentLoaded', () => {
    const heroSection = document.querySelector('.news-hero');
    const heroTitleEl = document.getElementById('newsHeroTitle');
    const heroSummaryEl = document.getElementById('newsHeroSummary');
    const heroDateEl = document.getElementById('newsHeroDate');
    const heroButton = document.getElementById('newsHeroReadMore');

    const highlightsContainer = document.getElementById('newsHighlights');
    const highlightsEmptyState = document.getElementById('newsHighlightsEmpty');
    const listContainer = document.getElementById('newsGrid');
    const listEmptyState = document.getElementById('newsListEmpty');
    const paginationContainer = document.getElementById('newsPagination');
    const searchForm = document.getElementById('newsSearchForm');
    const searchInput = document.getElementById('newsSearchInput');
    const refreshButton = document.getElementById('refreshNewsBtn');

    const modalTitle = document.getElementById('newsModalTitle');
    const modalMeta = document.getElementById('newsModalMeta');
    const modalImage = document.getElementById('newsModalImage');
    const modalContent = document.getElementById('newsModalContent');

    let paginaAtual = 1;
    const itensPorPagina = 6;
    let termoBusca = '';
    let destaqueAtual = null;

    const usuario = getUsuarioLogado?.();
    if (usuario) {
        document.getElementById('userName').textContent = usuario.nome;
        const loginLink = document.querySelector('a.dropdown-item[href="/admin/login.html"]');
        if (loginLink) {
            loginLink.classList.add('d-none');
        }
    }

    heroButton.addEventListener('click', () => {
        if (destaqueAtual) {
            abrirModal(destaqueAtual);
        }
    });

    refreshButton.addEventListener('click', () => {
        carregarDestaques();
        carregarLista(paginaAtual);
    });

    searchForm.addEventListener('submit', event => {
        event.preventDefault();
        termoBusca = searchInput.value.trim();
        paginaAtual = 1;
        carregarLista(paginaAtual);
    });

    async function carregarDestaques() {
        setAriaBusy(highlightsContainer, true);
        try {
            const resposta = await chamarAPI(`/noticias?destaque=true&per_page=5`);
            const noticias = resposta.items || [];
            if (noticias.length > 0) {
                destaqueAtual = noticias[0];
                atualizarHero(destaqueAtual);
                renderizarHighlights(noticias.slice(1));
            } else {
                destaqueAtual = null;
                atualizarHero();
                renderizarHighlights([]);
            }
        } catch (error) {
            console.error('Erro ao carregar destaques', error);
            showToast('Não foi possível carregar os destaques de notícias.', 'danger');
        } finally {
            setAriaBusy(highlightsContainer, false);
        }
    }

    async function carregarLista(pagina = 1) {
        setAriaBusy(listContainer, true);
        try {
            const params = new URLSearchParams({
                page: pagina.toString(),
                per_page: itensPorPagina.toString()
            });
            if (termoBusca) {
                params.append('busca', termoBusca);
            }
            const resposta = await chamarAPI(`/noticias?${params.toString()}`);
            const noticias = resposta.items || [];
            if (noticias.length === 0) {
                listContainer.innerHTML = '';
                listEmptyState.classList.remove('visually-hidden');
            } else {
                listEmptyState.classList.add('visually-hidden');
                listContainer.innerHTML = noticias.map(criarCardNoticia).join('');
                listContainer.querySelectorAll('[data-news-id]').forEach(botao => {
                    botao.addEventListener('click', () => {
                        const id = Number.parseInt(botao.getAttribute('data-news-id'), 10);
                        const noticia = noticias.find(item => item.id === id);
                        if (noticia) {
                            abrirModal(noticia);
                        }
                    });
                });
            }
            paginaAtual = resposta.page || pagina;
            renderizarPaginacao(resposta.pages || 1, paginaAtual);
        } catch (error) {
            console.error('Erro ao carregar notícias', error);
            showToast('Erro ao carregar notícias. Tente novamente em instantes.', 'danger');
        } finally {
            setAriaBusy(listContainer, false);
        }
    }

    function atualizarHero(noticia) {
        if (!noticia) {
            heroTitleEl.textContent = 'Nenhum destaque disponível por enquanto';
            heroSummaryEl.textContent = 'Volte em breve para conferir as novidades da unidade.';
            heroDateEl.textContent = '';
            heroButton.disabled = true;
            heroSection.style.backgroundImage = '';
            return;
        }
        heroTitleEl.textContent = noticia.titulo;
        heroSummaryEl.textContent = noticia.resumo;
        heroDateEl.textContent = formatarDataHumana(noticia.data_publicacao);
        heroDateEl.classList.remove('visually-hidden');
        heroButton.disabled = false;
        if (noticia.imagem_url) {
            heroSection.style.backgroundImage = `linear-gradient(135deg, rgba(22, 65, 148, 0.75), rgba(0, 139, 210, 0.65)), url('${encodeURI(noticia.imagem_url)}')`;
            heroSection.style.backgroundSize = 'cover';
            heroSection.style.backgroundPosition = 'center';
        } else {
            heroSection.style.backgroundImage = 'linear-gradient(135deg, rgba(22,65,148,0.95), rgba(0,139,210,0.9))';
        }
    }

    function renderizarHighlights(noticias) {
        if (!noticias || noticias.length === 0) {
            highlightsContainer.innerHTML = '';
            highlightsEmptyState.classList.remove('visually-hidden');
            return;
        }
        highlightsEmptyState.classList.add('visually-hidden');
        highlightsContainer.innerHTML = noticias.map(criarHighlightNoticia).join('');
        highlightsContainer.querySelectorAll('[data-news-id]').forEach(botao => {
            botao.addEventListener('click', event => {
                event.preventDefault();
                const id = Number.parseInt(botao.getAttribute('data-news-id'), 10);
                const noticia = noticias.find(item => item.id === id);
                if (noticia) {
                    abrirModal(noticia);
                }
            });
        });
    }

    function criarHighlightNoticia(noticia) {
        const resumo = noticia.resumo ?? '';
        return `
            <article class="news-highlight" role="listitem" tabindex="0">
                <p class="news-highlight__date mb-1">${formatarDataHumana(noticia.data_publicacao)}</p>
                <h3 class="news-highlight__title">${escapeHTML(noticia.titulo)}</h3>
                <p class="news-highlight__excerpt">${escapeHTML(resumo)}</p>
                <button class="btn btn-link p-0 mt-2" data-news-id="${noticia.id}" aria-label="Ler notícia ${escapeHTML(noticia.titulo)}">
                    Ler mais <i class="bi bi-arrow-right-short"></i>
                </button>
            </article>
        `;
    }

    function criarCardNoticia(noticia) {
        const imagem = noticia.imagem_url ? `<img class="news-card__image" src="${encodeURI(noticia.imagem_url)}" alt="Imagem ilustrativa da notícia">` : '<div class="news-card__image" role="presentation"></div>';
        return `
            <article class="news-card" role="listitem">
                ${imagem}
                <div class="news-card__body">
                    <time class="news-card__date" datetime="${escapeHTML(noticia.data_publicacao || '')}">${formatarDataHumana(noticia.data_publicacao)}</time>
                    <h3 class="news-card__title">${escapeHTML(noticia.titulo)}</h3>
                    <p class="news-card__summary">${escapeHTML(noticia.resumo ?? '')}</p>
                    <div class="news-card__actions">
                        <button class="btn btn-outline-primary" type="button" data-news-id="${noticia.id}" aria-label="Abrir notícia ${escapeHTML(noticia.titulo)}">
                            <i class="bi bi-journal-text me-1"></i> Ler notícia
                        </button>
                    </div>
                </div>
            </article>
        `;
    }

    function renderizarPaginacao(totalPaginas, pagina) {
        paginationContainer.innerHTML = '';
        if (totalPaginas <= 1) return;
        const criarItem = (label, targetPage, disabled = false, active = false) => `
            <li class="page-item ${disabled ? 'disabled' : ''} ${active ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${targetPage}">${label}</a>
            </li>
        `;
        paginationContainer.insertAdjacentHTML('beforeend', criarItem('Anterior', pagina - 1, pagina <= 1));
        for (let i = 1; i <= totalPaginas; i++) {
            paginationContainer.insertAdjacentHTML('beforeend', criarItem(i, i, false, i === pagina));
        }
        paginationContainer.insertAdjacentHTML('beforeend', criarItem('Próxima', pagina + 1, pagina >= totalPaginas));
        paginationContainer.querySelectorAll('a[data-page]').forEach(link => {
            link.addEventListener('click', event => {
                event.preventDefault();
                const alvo = Number.parseInt(link.getAttribute('data-page'), 10);
                if (!Number.isNaN(alvo) && alvo >= 1 && alvo <= totalPaginas && alvo !== paginaAtual) {
                    paginaAtual = alvo;
                    carregarLista(paginaAtual);
                    window.scrollTo({ top: document.getElementById('newsListHeading').offsetTop - 80, behavior: 'smooth' });
                }
            });
        });
    }

    function abrirModal(noticia) {
        modalTitle.textContent = noticia.titulo;
        const dataPublicacao = formatarDataHumana(noticia.data_publicacao);
        const autor = noticia.autor ? ` | ${escapeHTML(noticia.autor)}` : '';
        modalMeta.textContent = `${dataPublicacao}${autor}`;
        if (noticia.imagem_url) {
            modalImage.src = noticia.imagem_url;
            modalImage.alt = `Imagem ilustrativa da notícia ${noticia.titulo}`;
            modalImage.classList.remove('d-none');
        } else {
            modalImage.classList.add('d-none');
            modalImage.removeAttribute('src');
        }
        modalContent.innerHTML = sanitizeHTML?.(noticia.conteudo ?? '') || escapeHTML(noticia.conteudo ?? '');
    }

    function formatarDataHumana(dataISO) {
        if (!dataISO) return 'Data não informada';
        try {
            const data = new Date(dataISO);
            return data.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' });
        } catch (error) {
            return 'Data não informada';
        }
    }

    function setAriaBusy(elemento, ocupado) {
        if (!elemento) return;
        elemento.setAttribute('aria-busy', ocupado ? 'true' : 'false');
    }

    function escapeHTML(texto = '') {
        const div = document.createElement('div');
        div.textContent = texto;
        return div.innerHTML;
    }

    carregarDestaques();
    carregarLista(paginaAtual);
});
