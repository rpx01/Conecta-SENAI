// Arquivo JavaScript global para o Sistema de Agenda de Laboratório
// Contém funções de autenticação, manipulação de localStorage e utilitários

// Constantes globais
const API_URL = '/api';

/**
 * Escapa caracteres HTML para prevenir ataques XSS.
 * @param {string} str - Texto a escapar
 * @returns {string} - HTML escapado
 */
function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}

function sanitizeHTML(html) {
    return window.DOMPurify ? DOMPurify.sanitize(html) : html;
}

// Funções de autenticação
/**
 * Realiza o login do usuário
 * @param {string} email - Email do usuário
 * @param {string} senha - Senha do usuário
 * @returns {Promise} - Promise com o resultado do login
 */
async function realizarLogin(email, senha, recaptchaToken = '') {
    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, senha, recaptcha_token: recaptchaToken })
        });
        const contentType = response.headers.get('Content-Type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json().catch(() => null);

            console.log('Login response JSON:', response.status, data);

            if (response.ok && data) {
                // Armazena os dados do usuário no localStorage
                localStorage.setItem('usuario', JSON.stringify(data.usuario));
                localStorage.setItem('isAdmin', data.usuario.tipo === 'admin');

                // Após o login, redireciona sempre para a página de seleção de sistema
                window.location.href = '/selecao-sistema.html';
                return data;
            }

            if (!response.ok) {
                if (response.status >= 500) {
                    throw new Error('Servidor temporariamente indisponível');
                }
                const msg = data?.erro || data?.error || data?.message || 'Usuário ou senha inválidos';
                throw new Error(msg);
            }

            throw new Error('Resposta inesperada do servidor');
        }

        const texto = await response.text();
        console.error('Login response text:', response.status, texto);
        throw new Error('Erro interno no servidor. Tente mais tarde.');
    } catch (error) {
        console.error('Erro no login:', error);
        if (error.name === 'TypeError') {
            // Erro de rede ou CORS
            throw new Error('Erro de conexão com o servidor');
        }
        throw error;
    }
}

/**
 * Realiza o logout do usuário
 */
function realizarLogout() {
    fetch(`${API_URL}/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    }).catch(() => {});
    localStorage.removeItem('usuario');
    window.location.href = '/admin-login.html';
}

/**
 * Verifica se o usuário está autenticado
 * @returns {boolean} - True se autenticado, false caso contrário
 */
/**
 * Obtém os dados do usuário logado
 * @returns {Object|null} - Objeto com os dados do usuário ou null se não estiver autenticado
 */
function getUsuarioLogado() {
    const usuarioJSON = localStorage.getItem('usuario');
    return usuarioJSON ? JSON.parse(usuarioJSON) : null;
}

/**
 * Verifica se o usuário logado é administrador
 * @returns {boolean} - True se for administrador, false caso contrário
 */
function isAdmin() {
    const usuario = getUsuarioLogado();
    return usuario && usuario.tipo === 'admin';
}

function isUserAdmin() {
    return localStorage.getItem('isAdmin') === 'true';
}

// Função para ajustar a visibilidade dos elementos com base no papel do usuário
function ajustarVisibilidadePorPapel() {
    // A função isAdmin() já deve existir no seu app.js e ler do localStorage
    if (!isAdmin()) {
        // Encontra todos os elementos que são apenas para administradores
        const adminElements = document.querySelectorAll('.admin-only');

        // Oculta cada um deles
        adminElements.forEach(el => {
            el.style.display = 'none';
        });
    }
}

/**
 * Redireciona para a página de login se o usuário não estiver autenticado
 */
function verificarAutenticacao() {
    const usuario = getUsuarioLogado();
    if (!usuario) {
        window.location.href = '/admin-login.html';
        return false;
    }
    return true;
}

/**
 * Verifica se o usuário tem permissão de administrador
 * Redireciona para o dashboard se não tiver
 */
function verificarPermissaoAdmin() {
    // Passo 1: Verifica se o usuário está autenticado. Se não, a função já redireciona.
    if (!verificarAutenticacao()) return false;

    // Passo 2: Verifica se a página atual é a de seleção de sistema.
    const paginaAtual = window.location.pathname;
    if (paginaAtual === '/selecao-sistema.html') {
        // Se for a página de seleção, NÃO FAÇA NADA. Permita o acesso.
        return true;
    }

    // Passo 3: Se NÃO for a página de seleção, continue com a verificação de admin.
    if (!isAdmin()) {
        alert('Acesso não autorizado');
        window.location.href = '/selecao-sistema.html'; // Redireciona para um local seguro
        return false;
    }

    return true;
}

// ---------- Proteção de Rotas Global ----------
// Esta IIFE garante que o redirecionamento ocorra apenas quando necessário,
// evitando loops na página de login ou registro.
(function() {
    const currentPage = window.location.pathname;
    const loginPage = '/admin-login.html';
    const registerPage = '/register.html';
    const usuario = getUsuarioLogado();

    if (usuario) {
        // Se estiver autenticado e na página pública, envia para o dashboard adequado
        if (currentPage === loginPage || currentPage === registerPage) {
            if (usuario.tipo === 'admin') {
                window.location.href = '/selecao-sistema.html';
            } else {
                window.location.href = '/index.html';
            }
        }
    } else {
        // Não autenticado: redireciona para o login caso tente acessar página protegida
        if (currentPage !== loginPage && currentPage !== registerPage) {
            window.location.href = loginPage;
        }
    }
})();

// Funções para chamadas à API
/**
 * Realiza uma chamada à API com autenticação
 * @param {string} endpoint - Endpoint da API
 * @param {string} method - Método HTTP (GET, POST, PUT, DELETE)
 * @param {Object} body - Corpo da requisição (opcional)
 * @returns {Promise} - Promise com o resultado da chamada
 */
async function chamarAPI(endpoint, method = 'GET', body = null, requerAuth = true) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    // Garante que o endpoint comece com /
    const endpointFormatado = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${API_URL}${endpointFormatado}`;
    
    
    const options = {
        method,
        headers,
        credentials: 'include'
    };
    
    if (body && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(body);
    }
    
    try {
        let response = await fetch(url, options);

        // Verifica se a resposta indica falta de autorização e redireciona imediatamente
        if (response.status === 401) {
            localStorage.removeItem('usuario');
            window.location.href = '/admin-login.html';
            throw new Error('Sessão expirada');
        }

        if (!response.ok) {
            let mensagemErro = `Erro ${response.status}`;

            const data = await response.json().catch(() => ({}));
            const detalhe = data.erro || data.detail;

            // Verifica se o detalhe do erro é uma lista (padrão de erros de validação)
            if (Array.isArray(detalhe)) {
                // Mapeia a lista de objetos de erro para uma única string legível
                mensagemErro = detalhe
                    .map(e => {
                        if (e.loc && e.msg) {
                            return `${e.loc.join(' → ')}: ${e.msg}`;
                        }
                        return JSON.stringify(e);
                    })
                    .join('; ');
            } else if (detalhe) {
                mensagemErro = detalhe;
            }

            throw new Error(mensagemErro);
        }

        const data = await response.json().catch(() => ({}));
        return data;
    } catch (error) {
        console.error(`Erro na chamada à API ${url}:`, error);
        throw error;
    }
}

// Funções de formatação e utilidades
/**
 * Formata uma data no padrão brasileiro
 * @param {string} dataISO - Data em formato ISO
 * @returns {string} - Data formatada (DD/MM/YYYY)
 */
function formatarData(dataISO) {
    if (!dataISO) return '';
    const [parteData] = dataISO.split('T');
    const data = new Date(`${parteData}T00:00:00-03:00`);
    return data.toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo' });
}

/**
 * Formata um horário no padrão 24h
 * @param {string} horario - Horário em formato HH:MM
 * @returns {string} - Horário formatado
 */
function formatarHorario(horario) {
    if (!horario) return '';

    // Se já estiver no formato correto HH:MM, apenas normaliza zeros à esquerda
    const partes = horario.split(':');
    if (partes.length === 2) {
        const horas = parseInt(partes[0], 10);
        const minutos = parseInt(partes[1], 10);

        if (!isNaN(horas) && !isNaN(minutos)) {
            const h = String(horas).padStart(2, '0');
            const m = String(minutos).padStart(2, '0');
            return `${h}:${m}`;
        }
    }

    // Caso não seja possível formatar, retorna original
    return horario;
}

/**
 * Exibe uma mensagem de alerta na página
 * @param {string} mensagem - Mensagem a ser exibida
 * @param {string} tipo - Tipo de alerta (success, danger, warning, info)
 * @param {string} containerId - ID do container onde o alerta será exibido
 */
function exibirAlerta(mensagem, tipo = 'info', containerId = 'alertContainer') {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) return;

    const toastId = `toast-${Date.now()}`;
    const bgColor =
        tipo === 'danger' ? 'bg-danger' :
        (tipo === 'success' ? 'bg-success' : 'bg-primary');

    const toastHtml = `
        <div id="${toastId}" class="toast text-white ${bgColor}" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="5000">
            <div class="d-flex">
                <div class="toast-body">
                    ${escapeHTML(mensagem)}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>`;

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);

    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });

    toast.show();
}

/**
 * Retorna a classe CSS correspondente ao turno
 * @param {string} turno - Nome do turno (Manhã, Tarde, Noite)
 * @returns {string} - Nome da classe CSS
 */
function getClasseTurno(turno) {
    switch (turno) {
        case 'Manhã':
            return 'agendamento-manha';
        case 'Tarde':
            return 'agendamento-tarde';
        case 'Noite':
            return 'agendamento-noite';
        default:
            return '';
    }
}

/**
 * Adiciona o link para a página de Laboratórios e Turmas no menu
 * @param {string} containerSelector - Seletor CSS do container do menu
 * @param {boolean} isNavbar - Indica se é o menu da navbar ou sidebar
 */
function adicionarLinkLabTurmas(containerSelector, isNavbar = false) {
    const container = document.querySelector(containerSelector);
    if (!container) return;
    
    // Verifica se o link já existe para evitar duplicação
    const linkExistente = container.querySelector('a[href="/laboratorios-turmas.html"]');
    if (linkExistente) return;
    
    // Cria o elemento do link baseado no tipo de menu
    if (isNavbar) {
        // Para navbar (menu superior)
        const navItem = document.createElement('li');
        navItem.className = 'nav-item admin-only';
        
        const link = document.createElement('a');
        link.className = 'nav-link';
        link.href = '/laboratorios-turmas.html';
        link.innerHTML = '<i class="bi bi-building me-1"></i> Laboratórios e Turmas';
        
        navItem.appendChild(link);
        
        // Insere antes do último item (dropdown do usuário)
        const lastItem = container.querySelector('.dropdown');
        if (lastItem) {
            container.insertBefore(navItem, lastItem);
        } else {
            container.appendChild(navItem);
        }
    } else {
        // Para sidebar (menu lateral)
        const link = document.createElement('a');
        link.className = 'nav-link admin-only';
        link.href = '/laboratorios-turmas.html';
        link.innerHTML = '<i class="bi bi-building"></i> Laboratórios e Turmas';
        
        // Insere antes do último item (Meu Perfil)
        const lastItem = container.querySelector('a[href="/perfil.html"], a[href="/perfil-salas.html"], a[href="/perfil-usuarios.html"]');
        if (lastItem) {
            container.insertBefore(link, lastItem);
        } else {
            container.appendChild(link);
        }
    }
}

// Adiciona o link para a página de Logs
function adicionarLinkLogs(containerSelector, isNavbar = false) {
    const container = document.querySelector(containerSelector);
    if (!container) return;

    const linkExistente = container.querySelector('a[href="/logs-agenda.html"]');
    if (linkExistente) return;

    if (isNavbar) {
        const navItem = document.createElement('li');
        navItem.className = 'nav-item admin-only';

        const link = document.createElement('a');
        link.className = 'nav-link';
        link.href = '/logs-agenda.html';
        link.innerHTML = '<i class="bi bi-journal-text me-1"></i> Logs';

        navItem.appendChild(link);

        const lastItem = container.querySelector('.dropdown');
        if (lastItem) {
            container.insertBefore(navItem, lastItem);
        } else {
            container.appendChild(navItem);
        }
    } else {
        const link = document.createElement('a');
        link.className = 'nav-link admin-only';
        link.href = '/logs-agenda.html';
        link.innerHTML = '<i class="bi bi-journal-text"></i> Logs';

        const lastItem = container.querySelector('a[href="/perfil.html"], a[href="/perfil-salas.html"], a[href="/perfil-usuarios.html"]');
        if (lastItem) {
            container.insertBefore(link, lastItem);
        } else {
            container.appendChild(link);
        }
    }
}

/**
 * Adiciona ao menu do usuário um botão para retornar à tela de seleção de sistema
 */
function adicionarBotaoSelecaoSistema() {
    if (!isAdmin()) return;

    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        // Evita duplicação do botão
        if (menu.querySelector('a[href="/selecao-sistema.html"]')) return;

        const li = document.createElement('li');
        li.className = 'admin-only';

        const link = document.createElement('a');
        link.className = 'dropdown-item';
        link.href = '/selecao-sistema.html';
        link.innerHTML = '<i class="bi bi-arrow-return-left me-2"></i> Retornar à tela de seleção de sistema';

        li.appendChild(link);

        const logoutLink = menu.querySelector('#btnLogout') || menu.querySelector('a[onclick="realizarLogout()"]');
        if (logoutLink && logoutLink.parentElement) {
            menu.insertBefore(li, logoutLink.parentElement);
        } else {
            menu.appendChild(li);
        }
    });
}

// Inicialização da página
document.addEventListener('DOMContentLoaded', function() {
    
    // Verifica autenticação em todas as páginas exceto login e registro
    const paginaAtual = window.location.pathname;
    
    // Configura o botão de logout em todas as páginas
    const btnLogout = document.getElementById('btnLogout');
    if (btnLogout) {
        btnLogout.addEventListener('click', function(e) {
            e.preventDefault();
            realizarLogout();
        });
    }
    
    if (paginaAtual === '/admin-login.html' || paginaAtual === '/register.html') {
        return;
    }
    
    // Verifica se o usuário está autenticado
    if (!verificarAutenticacao()) {
        return;
    }


    
    // Verifica se é a página de seleção de sistema
    if (paginaAtual === '/selecao-sistema.html') {
        if (!verificarPermissaoAdmin()) {
            return;
        }
        return;
    }
    
    // Páginas que requerem permissão de administrador
    if (paginaAtual === '/usuarios.html' || paginaAtual === '/laboratorios-turmas.html') {
        if (!verificarPermissaoAdmin()) {
            return;
        }
    }
    
    // Adiciona o botão de retorno para admins
    adicionarBotaoSelecaoSistema();

    // Atualiza a interface com os dados do usuário
    atualizarInterfaceUsuario();

    // CHAMA A NOVA FUNÇÃO PARA AJUSTAR A INTERFACE
    ajustarVisibilidadePorPapel();
    
    // Adiciona o link para Laboratórios e Turmas somente no módulo de Agenda
    if (isAdmin()) {
        const paginasOcupacao = [
            '/dashboard-salas.html',
            '/calendario-salas.html',
            '/gerenciar-salas.html',
            '/corpo-docente.html',
            '/novo-agendamento-sala.html',
            '/perfil-rateio.html',
            '/rateio-lancamentos.html',
            '/rateio-config.html',
            '/rateio-instrutores.html',
            '/perfil-salas.html',
            '/usuarios.html',
            '/perfil.html',
            '/perfil-usuarios.html',
            '/gerenciar-turmas.html',
            '/logs-rateio.html',
            '/treinamentos/portal.html',
            '/treinamentos/meus-treinamentos.html',
            '/treinamentos/catalogo-treinamentos.html',
            '/treinamentos/gestao-turmas.html',
            '/treinamentos/dashboard-treinamentos.html',
            '/treinamentos/participantes-turma.html'
        ];

        if (!paginasOcupacao.includes(paginaAtual)) {
            adicionarLinkLabTurmas('.navbar-nav.ms-auto', true);
            adicionarLinkLabTurmas('.sidebar .nav.flex-column', false);

            adicionarLinkLogs('.navbar-nav.ms-auto', true);
            adicionarLinkLogs('.sidebar .nav.flex-column', false);

            configurarObservadoresMenu();
        }
    }
});

/**
 * Configura observadores de mutação para garantir que os links admin sejam adicionados
 * mesmo quando o DOM é modificado dinamicamente
 */
function configurarObservadoresMenu() {
    // Configura o observador para a navbar
    const navbarObserver = new MutationObserver(function(mutations) {
        adicionarLinkLabTurmas('.navbar-nav.ms-auto', true);
        adicionarLinkLogs('.navbar-nav.ms-auto', true);
    });

    const navbar = document.querySelector('.navbar-nav.ms-auto');
    if (navbar) {
        navbarObserver.observe(navbar, { childList: true, subtree: true });
    }

    // Configura o observador para a sidebar
    const sidebarObserver = new MutationObserver(function(mutations) {
        adicionarLinkLabTurmas('.sidebar .nav.flex-column', false);
        adicionarLinkLogs('.sidebar .nav.flex-column', false);
    });
    
    const sidebar = document.querySelector('.sidebar .nav.flex-column');
    if (sidebar) {
        sidebarObserver.observe(sidebar, { childList: true, subtree: true });
    }
}

/**
 * Atualiza elementos da interface com os dados do usuário logado
 */
function atualizarInterfaceUsuario() {
    const usuario = getUsuarioLogado();
    if (!usuario) return;
    
    // Atualiza o nome do usuário na navbar
    const userNameElement = document.getElementById('userName');
    if (userNameElement) {
        userNameElement.textContent = usuario.nome;
    }
    
    // Exibe ou oculta elementos baseado no tipo de usuário
    const adminElements = document.querySelectorAll('.admin-only');
    adminElements.forEach(element => {
        element.style.display = isAdmin() ? '' : 'none';
    });
    
    // Carrega notificações no dashboard
    if (window.location.pathname === '/index.html') {
        carregarNotificacoes();
    }
}

/**
 * Carrega notificações do usuário para exibição no dashboard
 */
async function carregarNotificacoes() {
    const notificacoesContainer = document.getElementById('notificacoesContainer');
    if (!notificacoesContainer) return;
    
    try {
        const notificacoes = await chamarAPI('/notificacoes');
        
        if (notificacoes.length === 0) {
            notificacoesContainer.innerHTML = '<p class="text-muted">Nenhuma notificação disponível.</p>';
            return;
        }
        
        let html = '';
        notificacoes.forEach(notificacao => {
            const classeNotificacao = notificacao.lida ? 'bg-light' : 'bg-info bg-opacity-10';
            html += `
                <div class="card mb-2 ${classeNotificacao}">
                    <div class="card-body">
                        <p class="card-text">${notificacao.mensagem}</p>
                        <p class="card-text"><small class="text-muted">
                            ${formatarData(notificacao.data_criacao)}
                        </small></p>
                        ${!notificacao.lida ? `
                            <button class="btn btn-sm btn-outline-primary marcar-lida" 
                                data-id="${notificacao.id}">Marcar como lida</button>
                        ` : ''}
                    </div>
                </div>
            `;
        });
        
        notificacoesContainer.innerHTML = html;
        
        // Adiciona event listeners para os botões de marcar como lida
        document.querySelectorAll('.marcar-lida').forEach(btn => {
            btn.addEventListener('click', async function() {
                const id = this.getAttribute('data-id');
                try {
                    await chamarAPI(`/notificacoes/${id}/marcar-lida`, 'PUT');
                    // Recarrega as notificações
                    carregarNotificacoes();
                } catch (error) {
                    exibirAlerta('Erro ao marcar notificação como lida', 'danger');
                }
            });
        });
    } catch (error) {
        notificacoesContainer.innerHTML = '<p class="text-danger">Erro ao carregar notificações.</p>';
    }
}

/**
 * Carrega laboratórios do sistema para uso em filtros e formulários
 * @returns {Promise<Array>} - Promise com a lista de laboratórios
 */
async function carregarLaboratoriosParaFiltro(seletorElemento) {
    const selectElement = document.querySelector(seletorElemento);
    if (!selectElement) return [];
    
    try {
        const laboratorios = await chamarAPI('/laboratorios');
        
        // Mantém a opção "Todos"
        let html = '<option value="">Todos</option>';
        
        // Adiciona as opções de laboratórios
        laboratorios.forEach(lab => {
            html += `<option value="${lab.nome}">${lab.nome}</option>`;
        });
        
        selectElement.innerHTML = html;
        return laboratorios;
    } catch (error) {
        console.error('Erro ao carregar laboratórios para filtro:', error);
        return [];
    }
}

// Exporta dados genéricos (CSV, PDF ou XLSX)
async function exportarDados(endpoint, formato, nomeArquivo) {
    try {
        const response = await fetch(`${API_URL}${endpoint}?formato=${formato}`, {
        });
        if (!response.ok) {
            throw new Error('Erro ao exportar dados');
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${nomeArquivo}.${formato}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Erro ao exportar dados:', error);
        exibirAlerta('Falha ao exportar dados', 'danger');
    }
}

// Preenche de forma genérica uma tabela a partir de um endpoint
async function preencherTabela(idTabela, endpoint, funcaoRenderizarLinha) {
    const tabela = document.getElementById(idTabela);
    if (!tabela) {
        console.error(`Tabela com id '${idTabela}' não encontrada.`);
        return [];
    }
    const thead = tabela.querySelector('thead');
    const tbody = tabela.querySelector('tbody');
    const numColunas = thead ? thead.querySelector('tr').childElementCount : 1;

    // Exibe o spinner centralizado enquanto os dados são carregados
    tbody.innerHTML = `
        <tr>
            <td colspan="${numColunas}" class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
            </td>
        </tr>`;

    try {
        const dados = await chamarAPI(endpoint, 'GET');
        tbody.innerHTML = '';
        if (dados && dados.length > 0) {
            dados.forEach(item => {
                const linhaHtml = funcaoRenderizarLinha(item);
                if (linhaHtml) {
                    tbody.insertAdjacentHTML('beforeend', linhaHtml);
                }
            });
        } else {
            tbody.innerHTML = `<tr><td colspan="${numColunas}" class="text-center">Nenhum registro encontrado.</td></tr>`;
        }
        return dados;
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="${numColunas}" class="text-center text-danger">Erro ao carregar os dados.</td></tr>`;
        console.error(`Erro ao preencher tabela ${idTabela}:`, error);
        return [];
    }
}
