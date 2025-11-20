/**
 * CONECTA SENAI - System Selection Page JavaScript
 * Handles search, filtering, toggle switch, keyboard navigation, and quick access
 */

(function() {
    'use strict';

    // State management
    let allModules = [];
    let currentFilter = 'all';
    let searchQuery = '';

    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        // Authentication check
        if (!verificarAutenticacao()) return;

        initializeUserMenu();
        initializeModules();
        initializeSearch();
        initializeCategoryFilters();
        initializeToggleSwitch();
        initializeKeyboardShortcuts();
        initializeQuickAccess();
        setupLogout();
    });

    /**
     * Initialize user menu with role and status
     */
    function initializeUserMenu() {
        const usuario = getUsuarioLogado();
        if (!usuario) return;

        const userName = document.getElementById('userName');
        if (userName) {
            userName.textContent = usuario.nome;
        }

        // Add user role if available
        const userRole = usuario.role || usuario.funcao || 'Usuário';
        const roleElement = document.querySelector('.user-role-badge');
        if (roleElement) {
            roleElement.textContent = userRole;
        }
    }

    /**
     * Initialize all module cards and collect them for filtering
     */
    function initializeModules() {
        const usuario = getUsuarioLogado();
        if (!usuario) return;

        const modulosDisponiveis = new Set(obterModulosDisponiveis(usuario));
        const moduleCards = document.querySelectorAll('[data-module-url]');

        moduleCards.forEach((card, index) => {
            const urlNormalizada = normalizarUrlModulo(card.getAttribute('data-module-url'));
            const hasPermission = urlNormalizada && modulosDisponiveis.has(urlNormalizada);
            
            // Store module data
            const moduleData = {
                element: card,
                url: card.getAttribute('data-module-url'),
                name: card.getAttribute('data-module-name') || '',
                description: card.getAttribute('data-module-description') || '',
                category: card.getAttribute('data-module-category') || 'all',
                hasPermission: hasPermission,
                index: index
            };
            allModules.push(moduleData);

            // Setup card based on permission
            if (!hasPermission) {
                card.classList.add('restricted');
                const enterBtn = card.querySelector('.btn-module-primary');
                if (enterBtn) {
                    enterBtn.disabled = true;
                }
            } else {
                // Add click handler for permitted modules
                const enterBtn = card.querySelector('.btn-module-primary');
                if (enterBtn) {
                    enterBtn.addEventListener('click', () => navigateToModule(moduleData));
                }
            }

            // Setup keyboard shortcut (1-9 for first 9 modules)
            if (hasPermission && index < 9) {
                const shortcut = index + 1;
                const hintElement = card.querySelector('.keyboard-hint');
                if (hintElement) {
                    hintElement.textContent = `Alt+${shortcut}`;
                }
            }
        });

        // Hide admin-only modules for non-admin users
        if (!isAdmin()) {
            document.querySelectorAll('.admin-only').forEach(el => {
                el.style.display = 'none';
            });
        }
    }

    /**
     * Initialize search functionality with debouncing
     */
    function initializeSearch() {
        const searchInput = document.getElementById('moduleSearch');
        if (!searchInput) return;

        let debounceTimer;
        searchInput.addEventListener('input', function(e) {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                searchQuery = e.target.value.toLowerCase().trim();
                filterModules();
            }, 300);
        });

        // Focus search with "/" keyboard shortcut
        document.addEventListener('keydown', function(e) {
            if (e.key === '/' && !isInputFocused()) {
                e.preventDefault();
                searchInput.focus();
            }
        });
    }

    /**
     * Initialize category filter buttons
     */
    function initializeCategoryFilters() {
        const filterButtons = document.querySelectorAll('.category-filter-btn');
        
        filterButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                // Update active state
                filterButtons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                // Update filter
                currentFilter = this.getAttribute('data-category');
                filterModules();
            });
        });
    }

    /**
     * Initialize toggle switch for module preference
     */
    function initializeToggleSwitch() {
        const toggleSwitch = document.getElementById('toggleSwitch');
        const clearLink = document.getElementById('clearPreference');
        
        if (!toggleSwitch) return;

        // Check if preference exists
        const savedModule = localStorage.getItem('moduloSelecionado');
        if (savedModule) {
            toggleSwitch.classList.add('active');
            if (clearLink) clearLink.style.display = 'inline-block';
        }

        // Toggle click handler
        toggleSwitch.addEventListener('click', function() {
            this.classList.toggle('active');
            
            const isActive = this.classList.contains('active');
            if (!isActive) {
                localStorage.removeItem('moduloSelecionado');
                if (clearLink) clearLink.style.display = 'none';
            }
            
            // Show toast notification
            showToast(isActive ? 
                'Sua preferência será salva ao selecionar um módulo' : 
                'Preferência removida. Você verá esta tela em cada login'
            );
        });

        // Clear preference link
        if (clearLink) {
            clearLink.addEventListener('click', function(e) {
                e.preventDefault();
                localStorage.removeItem('moduloSelecionado');
                toggleSwitch.classList.remove('active');
                this.style.display = 'none';
                showToast('Preferência de módulo removida');
            });
        }
    }

    /**
     * Initialize keyboard shortcuts for quick module access
     */
    function initializeKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ignore if user is typing in an input
            if (isInputFocused()) return;

            // Alt + Number (1-9) for quick access
            if (e.altKey && !e.ctrlKey && !e.shiftKey) {
                const num = parseInt(e.key);
                if (num >= 1 && num <= 9) {
                    e.preventDefault();
                    const module = allModules.find(m => m.index === num - 1 && m.hasPermission);
                    if (module) {
                        navigateToModule(module);
                    }
                }
            }

            // Escape to clear search and filters
            if (e.key === 'Escape') {
                clearSearchAndFilters();
            }
        });
    }

    /**
     * Initialize quick access feature for last used module
     */
    function initializeQuickAccess() {
        const savedModule = localStorage.getItem('moduloSelecionado');
        const quickAccessBtn = document.getElementById('quickAccessBtn');
        
        if (savedModule && quickAccessBtn) {
            // Check if user still has permission
            const usuario = getUsuarioLogado();
            const modulosDisponiveis = new Set(obterModulosDisponiveis(usuario));
            const urlNormalizada = normalizarUrlModulo(savedModule);
            
            if (urlNormalizada && modulosDisponiveis.has(urlNormalizada)) {
                quickAccessBtn.style.display = 'inline-flex';
                quickAccessBtn.addEventListener('click', function() {
                    window.location.href = savedModule;
                });
            } else {
                // Remove invalid preference
                localStorage.removeItem('moduloSelecionado');
            }
        }
    }

    /**
     * Filter modules based on search query and category
     */
    function filterModules() {
        let visibleCount = 0;
        const categories = new Set();

        allModules.forEach(module => {
            let isVisible = true;

            // Filter by category
            if (currentFilter !== 'all' && module.category !== currentFilter) {
                isVisible = false;
            }

            // Filter by search query
            if (searchQuery && isVisible) {
                const searchableText = `${module.name} ${module.description}`.toLowerCase();
                if (!searchableText.includes(searchQuery)) {
                    isVisible = false;
                }
            }

            // Show/hide module
            const container = module.element.closest('.col-md-4, .col-lg-4, .col-sm-6');
            if (container) {
                container.style.display = isVisible ? '' : 'none';
            }

            if (isVisible) {
                visibleCount++;
                categories.add(module.category);
            }
        });

        // Show/hide category sections
        document.querySelectorAll('.category-section').forEach(section => {
            const categoryName = section.getAttribute('data-category');
            const hasVisibleModules = categories.has(categoryName) || currentFilter === 'all';
            section.style.display = hasVisibleModules ? '' : 'none';
        });

        // Show no results message
        const noResults = document.getElementById('noResults');
        if (noResults) {
            noResults.style.display = visibleCount === 0 ? 'block' : 'none';
        }

        // Update module counts
        updateModuleCounts();
    }

    /**
     * Update module count badges in category headers
     */
    function updateModuleCounts() {
        document.querySelectorAll('.category-section').forEach(section => {
            const categoryName = section.getAttribute('data-category');
            const count = allModules.filter(m => {
                const matchesCategory = m.category === categoryName;
                const matchesSearch = !searchQuery || 
                    `${m.name} ${m.description}`.toLowerCase().includes(searchQuery);
                return matchesCategory && matchesSearch;
            }).length;

            const countBadge = section.querySelector('.module-count');
            if (countBadge) {
                countBadge.textContent = count;
            }
        });
    }

    /**
     * Navigate to a module and save preference if toggle is active
     */
    function navigateToModule(module) {
        const toggleSwitch = document.getElementById('toggleSwitch');
        
        // Save preference if toggle is active
        if (toggleSwitch && toggleSwitch.classList.contains('active')) {
            localStorage.setItem('moduloSelecionado', module.url);
        }

        // Navigate to module
        window.location.href = module.url;
    }

    /**
     * Clear search and filters
     */
    function clearSearchAndFilters() {
        const searchInput = document.getElementById('moduleSearch');
        if (searchInput) {
            searchInput.value = '';
        }
        
        searchQuery = '';
        currentFilter = 'all';
        
        // Reset filter buttons
        document.querySelectorAll('.category-filter-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-category') === 'all') {
                btn.classList.add('active');
            }
        });
        
        filterModules();
    }

    /**
     * Setup logout button
     */
    function setupLogout() {
        const logoutBtn = document.getElementById('btnLogout');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function(e) {
                e.preventDefault();
                realizarLogout();
            });
        }
    }

    /**
     * Check if an input element is currently focused
     */
    function isInputFocused() {
        const activeElement = document.activeElement;
        return activeElement && (
            activeElement.tagName === 'INPUT' ||
            activeElement.tagName === 'TEXTAREA' ||
            activeElement.tagName === 'SELECT' ||
            activeElement.isContentEditable
        );
    }

    /**
     * Show toast notification
     */
    function showToast(message) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--dark-color);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            z-index: 9999;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(toast);

        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

})();

// CSS animations for toast
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
    
    @media (max-width: 768px) {
        .toast-notification {
            right: 1rem !important;
            left: 1rem !important;
            bottom: 1rem !important;
        }
    }
`;
document.head.appendChild(style);
