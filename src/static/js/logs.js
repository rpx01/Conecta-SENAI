document.addEventListener('DOMContentLoaded', function() {
    const params = new URLSearchParams(window.location.search);
    const modelo = params.get('modelo');
    const titulo = params.get('titulo') || 'Auditoria';

    if (!modelo) {
        document.getElementById('logsTableBody').innerHTML = '<tr><td colspan="4">Erro: Modelo de log não especificado.</td></tr>';
        return;
    }

    document.getElementById('logPageTitle').textContent = `Logs de ${titulo}`;

    async function carregarLogs() {
        try {
            const logs = await chamarAPI(`/logs?modelo=${modelo}`);
            const tableBody = document.getElementById('logsTableBody');
            tableBody.innerHTML = '';

            logs.forEach(log => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${new Date(log.data_hora).toLocaleString('pt-BR')}</td>
                    <td>${escapeHTML(log.usuario_nome)}</td>
                    <td><span class="badge ${getBadgeClass(log.acao)}">${escapeHTML(log.acao)}</span></td>
                    <td>${formatarDetalhes(log)}</td>
                `;
                tableBody.appendChild(tr);
            });
        } catch (error) {
            exibirAlerta(`Erro ao carregar logs: ${error.message}`, 'danger');
        }
    }

    function formatarDetalhes(log) {
        if (log.acao === 'Criação' || log.acao === 'Exclusão') {
            return `Registo ${log.modelo_alvo} (ID: ${log.id_alvo}) foi ${log.acao === 'Criação' ? 'criado' : 'excluído'}.`;
        }
        if (log.acao === 'Atualização') {
            let html = '<ul>';
            for (const [chave, valores] of Object.entries(log.detalhes)) {
                html += `<li><strong>${chave}:</strong> de "<em>${escapeHTML(valores.de)}</em>" para "<em>${escapeHTML(valores.para)}</em>"</li>`;
            }
            html += '</ul>';
            return html;
        }
        return JSON.stringify(log.detalhes);
    }

    function getBadgeClass(acao) {
        switch(acao) {
            case 'Criação': return 'bg-success';
            case 'Atualização': return 'bg-warning text-dark';
            case 'Exclusão': return 'bg-danger';
            default: return 'bg-secondary';
        }
    }

    carregarLogs();
});

