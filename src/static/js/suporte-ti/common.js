(function(window) {
    const STATUS_LABELS = {
        aberto: 'Aberto',
        em_andamento: 'Em andamento',
        resolvido: 'Resolvido',
        encerrado: 'Encerrado'
    };

    const URGENCIA_LABELS = {
        baixa: 'Baixa',
        media: 'Média',
        alta: 'Alta',
        critica: 'Crítica'
    };

    const STATUS_BADGES = {
        aberto: 'badge-status-aberto',
        em_andamento: 'badge-status-em_andamento',
        resolvido: 'badge-status-resolvido',
        encerrado: 'badge-status-encerrado'
    };

    const URGENCIA_BADGES = {
        baixa: 'badge-urgencia-baixa',
        media: 'badge-urgencia-media',
        alta: 'badge-urgencia-alta',
        critica: 'badge-urgencia-critica'
    };

    function formatarStatus(status) {
        const chave = (status || '').toLowerCase();
        return STATUS_LABELS[chave] || status || '';
    }

    function formatarUrgencia(urgencia) {
        const chave = (urgencia || '').toLowerCase();
        return URGENCIA_LABELS[chave] || urgencia || '';
    }

    function obterBadgeStatus(status) {
        const chave = (status || '').toLowerCase();
        return STATUS_BADGES[chave] || 'bg-secondary';
    }

    function obterBadgeUrgencia(urgencia) {
        const chave = (urgencia || '').toLowerCase();
        return URGENCIA_BADGES[chave] || 'bg-secondary';
    }

    async function carregarAreas({ incluirInativas = false } = {}) {
        const query = incluirInativas ? '?ativo=' : '';
        return await chamarAPI(`/support/areas${query}`);
    }

    async function carregarEquipamentos({ incluirInativos = false } = {}) {
        const query = incluirInativos ? '?ativo=' : '';
        return await chamarAPI(`/support/equipamentos${query}`);
    }

    function preencherSelect(select, itens, { incluirOpcaoPadrao = true } = {}) {
        if (!select) return;
        select.innerHTML = '';
        if (incluirOpcaoPadrao) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Selecione...';
            select.appendChild(option);
        }
        itens.forEach(item => {
            const option = document.createElement('option');
            option.value = item.id;
            option.textContent = item.nome;
            if (item.ativo === false) {
                option.textContent += ' (inativo)';
                option.disabled = true;
            }
            select.appendChild(option);
        });
    }

    function criarBadge({ texto, classe }) {
        const span = document.createElement('span');
        span.className = `badge ${classe}`;
        span.textContent = texto;
        return span.outerHTML;
    }

    window.__suporteTI = {
        STATUS_LABELS,
        URGENCIA_LABELS,
        formatarStatus,
        formatarUrgencia,
        obterBadgeStatus,
        obterBadgeUrgencia,
        carregarAreas,
        carregarEquipamentos,
        preencherSelect,
        criarBadge
    };
})(window);
