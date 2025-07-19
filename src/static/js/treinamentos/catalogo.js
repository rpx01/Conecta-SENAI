document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/catalogo')
        .then(r => r.json())
        .then(treinamentos => {
            const tbody = document.getElementById('tabela-catalogo');
            if (!treinamentos.length) {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center">Nenhum treinamento cadastrado.</td></tr>';
                return;
            }
            tbody.innerHTML = treinamentos.map(t => `
                <tr>
                    <td>${escapeHTML(t.nome)}</td>
                    <td>${escapeHTML(t.codigo || '')}</td>
                    <td>${t.carga_horaria}h</td>
                    <td><a class="btn btn-sm btn-outline-primary" href="/treinamentos/editar/${t.id}">Editar</a></td>
                </tr>
            `).join('');
        })
        .catch(() => {
            const tbody = document.getElementById('tabela-catalogo');
            tbody.innerHTML = '<tr><td colspan="4" class="text-danger text-center">Erro ao carregar treinamentos.</td></tr>';
        });
});
