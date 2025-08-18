let geralModal;
let instrutorModal;

document.addEventListener('DOMContentLoaded', function () {
    const dataTableEl = document.querySelector('#basedadosTable');

    if (dataTableEl && window.simpleDatatables) {
        const dataTable = new simpleDatatables.DataTable(dataTableEl, {
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
                if (errorDiv) {
                    errorDiv.style.display = 'block';
                }
            });
    }

    const geralModalEl = document.getElementById('geralModal');
    if (geralModalEl) {
        geralModal = new bootstrap.Modal(geralModalEl);
    }

    const instrutorModalEl = document.getElementById('instrutorModal');
    if (instrutorModalEl) {
        instrutorModal = new bootstrap.Modal(instrutorModalEl);
    }
});

function abrirModal(type) {
    const labels = {
        treinamento: 'Treinamento',
        'publico-alvo': 'Público alvo',
        local: 'Local',
        modalidade: 'Modalidade',
        horario: 'Horário',
        cargahoraria: 'Carga Horária'
    };

    const titleEl = document.getElementById('geralModalLabel');
    const typeInput = document.getElementById('itemType');
    const nameInput = document.getElementById('itemName');

    if (titleEl) {
        titleEl.textContent = `Adicionar ${labels[type] || 'Item'}`;
    }

    if (typeInput) {
        typeInput.value = type;
    }

    if (nameInput) {
        nameInput.value = '';
    }

    if (geralModal) {
        geralModal.show();
    }
}

function abrirModalInstrutor() {
    const idInput = document.getElementById('instrutorId');
    const form = document.getElementById('formInstrutor');
    if (idInput) {
        idInput.value = '';
    }
    if (form) {
        form.reset();
    }
    if (instrutorModal) {
        instrutorModal.show();
    }
}

window.abrirModal = abrirModal;
window.abrirModalInstrutor = abrirModalInstrutor;
