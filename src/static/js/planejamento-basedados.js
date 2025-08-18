document.addEventListener('DOMContentLoaded', function () {
    const dataTable = new simpleDatatables.DataTable("#basedadosTable", {
        searchable: true,
        fixedHeight: true,
        labels: {
            placeholder: "Pesquisar...",
            perPage: "{select} entradas por página",
            noRows: "Nenhuma entrada encontrada",
            info: "Mostrando {start} a {end} de {rows} entradas",
        }
    });

    fetch('/planejamento/basedados/get')
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro na resposta da rede');
            }
            return response.json();
        })
        .then(data => {
            if (data.length === 0) {
                return;
            }

            const rows = data.map(item => {
                return [
                    item.id,
                    item.title,
                    item.description,
                    item.status,
                    item.created_at,
                    `<a href="/planejamento/basedados/${item.id}" class="btn btn-primary btn-sm">Ver</a>`
                ];
            });

            dataTable.insert({ data: rows });
        })
        .catch(error => {
            console.error('Erro ao buscar dados da base de dados:', error);
            const errorDiv = document.getElementById('error-message');
            errorDiv.style.display = 'block';
        });
});
