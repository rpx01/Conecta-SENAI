// Função para buscar e renderizar os dados do planejamento
async function fetchAndRenderPlanejamento() {
    try {
        const response = await fetch('/api/planejamento/all');
        if (!response.ok) {
            throw new Error('Erro ao buscar dados do planejamento');
        }
        const data = await response.json();
        renderPlanejamento(data); // Chama a função para renderizar a tabela
    } catch (error) {
        console.error('Erro:', error);
        Swal.fire('Erro!', 'Não foi possível carregar os dados do planejamento.', 'error');
    }
}

// Função para renderizar a tabela de planejamento
function renderPlanejamento(planejamentos) {
    const tabelaPlanejamento = document.getElementById('tabela-planejamento');
    const tbody = tabelaPlanejamento.querySelector('tbody');

    // 1. Limpa o corpo da tabela antes de adicionar novas linhas
    tbody.innerHTML = '';

    // 2. Itera sobre os itens do planejamento e cria uma linha para cada um
    planejamentos.forEach(item => {
        const tr = document.createElement('tr');

        // Formata as datas para o formato DD/MM/AAAA
        const dataInicial = item.data_inicial ? new Date(item.data_inicial).toLocaleDateString('pt-BR') : 'N/A';
        const dataFinal = item.data_final ? new Date(item.data_final).toLocaleDateString('pt-BR') : 'N/A';

        tr.innerHTML = `
            <td>${dataInicial}</td>
            <td>${dataFinal}</td>
            <td>${item.semana || 'N/A'}</td>
            <td>${item.horario || 'N/A'}</td>
            <td>${item.carga_horaria || 'N/A'}</td>
            <td>${item.modalidade || 'N/A'}</td>
            <td>${item.treinamento_nome || 'N/A'}</td>
            <td>${item.cmd || 'N/A'}</td>
            <td>${item.sjb || 'N/A'}</td>
            <td>${item.sag_tombos || 'N/A'}</td>
            <td>${item.instrutor_nome || 'N/A'}</td>
            <td>${item.local || 'N/A'}</td>
            <td>${item.observacao || ''}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editarItem(${item.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="excluirItem(${item.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}


// A função handleFormSubmit agora apenas salva e depois recarrega os dados
async function handleFormSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // Converte os valores para os tipos corretos se necessário
    data.carga_horaria = parseInt(data.carga_horaria, 10) || null;
    data.cmd = parseInt(data.cmd, 10) || null;
    data.sjb = parseInt(data.sjb, 10) || null;
    data.sag_tombos = parseInt(data.sag_tombos, 10) || null;

    try {
        const response = await fetch('/api/planejamento/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Erro ao salvar o item');
        }

        Swal.fire('Sucesso!', 'Item salvo com sucesso.', 'success');
        $('#addItemModal').modal('hide'); // Fecha o modal
        form.reset(); // Limpa o formulário
        fetchAndRenderPlanejamento(); // Recarrega e renderiza a tabela inteira

    } catch (error) {
        console.error('Erro ao salvar:', error);
        Swal.fire('Erro!', error.message, 'error');
    }
}

// ... (Restante do seu código JS, como as funções de editar, excluir e carregar dados nos modais)

// Carrega os dados iniciais quando a página é carregada
document.addEventListener('DOMContentLoaded', () => {
    fetchAndRenderPlanejamento();

    // Adiciona o listener para o formulário
    const addItemForm = document.getElementById('addItemForm');
    if (addItemForm) {
        addItemForm.addEventListener('submit', handleFormSubmit);
    }

    // ... (outros listeners que você possa ter)
});

// Suas funções editarItem, excluirItem, loadTreinamentos, loadInstrutores permanecem as mesmas.
// Apenas garanta que após uma exclusão, você chame fetchAndRenderPlanejamento() também.

async function excluirItem(id) {
    const result = await Swal.fire({
        title: 'Você tem certeza?',
        text: "Você não poderá reverter isso!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sim, excluir!',
        cancelButtonText: 'Cancelar'
    });

    if (result.isConfirmed) {
        try {
            const response = await fetch(`/api/planejamento/${id}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                throw new Error('Erro ao excluir o item.');
            }

            Swal.fire('Excluído!', 'O item foi excluído.', 'success');
            fetchAndRenderPlanejamento(); // Recarrega os dados
        } catch (error) {
            console.error('Erro ao excluir:', error);
            Swal.fire('Erro!', 'Não foi possível excluir o item.', 'error');
        }
    }
}

