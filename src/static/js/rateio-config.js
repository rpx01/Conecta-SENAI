// Conteudo atualizado para rateio-config.js

document.addEventListener('DOMContentLoaded', function() {
    // Validação de autenticação e permissões
    if (!verificarAutenticacao() || !isAdmin()) {
        window.location.href = '/selecao-sistema.html';
        return;
    }

    const configModal = new bootstrap.Modal(document.getElementById('configModal'));
    const confirmacaoModal = new bootstrap.Modal(document.getElementById('confirmacaoModal'));
    const form = document.getElementById('configForm');
    const tableBody = document.getElementById('configsTableBody');
    let configEmEdicaoId = null;
    let configParaExcluirId = null;

    // Função para carregar e renderizar as configurações
    async function carregarConfiguracoes() {
        try {
            const configs = await chamarAPI('/rateio-configs');
            tableBody.innerHTML = ''; // Limpa a tabela
            if (configs.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="6" class="text-center">Nenhuma configuração encontrada.</td></tr>`;
                return;
            }
            configs.forEach(config => {
                const tr = document.createElement('tr');
                tr.dataset.id = config.id;
                tr.innerHTML = `
                    <td>${escapeHTML(config.filial)}</td>
                    <td>${escapeHTML(config.uo)}</td>
                    <td>${escapeHTML(config.cr)}</td>
                    <td>${escapeHTML(config.classe_valor)}</td>
                    <td>${escapeHTML(config.descricao || '')}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary me-1 btn-editar" data-id="${config.id}" title="Editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger btn-excluir" data-id="${config.id}" title="Excluir">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                `;
                tableBody.appendChild(tr);
            });
        } catch (error) {
            exibirAlerta(`Erro ao carregar configurações: ${error.message}`, 'danger');
        }
    }

    // Função para abrir o modal em modo de edição ou criação
    function abrirModal(config = null) {
        form.reset();
        if (config) {
            configEmEdicaoId = config.id;
            document.getElementById('modalConfigLabel').textContent = 'Editar Configuração';
            document.getElementById('filial').value = config.filial;
            document.getElementById('uo').value = config.uo;
            document.getElementById('cr').value = config.cr;
            document.getElementById('classe_valor').value = config.classe_valor;
            document.getElementById('descricao').value = config.descricao || '';
        } else {
            configEmEdicaoId = null;
            document.getElementById('modalConfigLabel').textContent = 'Nova Configuração';
        }
        configModal.show();
    }

    // Salvar (Criar ou Editar)
    document.getElementById('btnSalvarConfig').addEventListener('click', async () => {
        const dados = {
            filial: document.getElementById('filial').value,
            uo: document.getElementById('uo').value,
            cr: document.getElementById('cr').value,
            classe_valor: document.getElementById('classe_valor').value,
            descricao: document.getElementById('descricao').value
        };

        try {
            if (configEmEdicaoId) {
                await chamarAPI(`/rateio-configs/${configEmEdicaoId}`, 'PUT', dados);
                exibirAlerta('Configuração atualizada com sucesso!', 'success');
            } else {
                await chamarAPI('/rateio-configs', 'POST', dados);
                exibirAlerta('Configuração criada com sucesso!', 'success');
            }
            configModal.hide();
            carregarConfiguracoes();
        } catch (error) {
            exibirAlerta(`Erro ao salvar: ${error.message}`, 'danger');
        }
    });

    // Lidar com cliques na tabela (delegação de eventos)
    tableBody.addEventListener('click', async (e) => {
        const btnEditar = e.target.closest('.btn-editar');
        const btnExcluir = e.target.closest('.btn-excluir');

        if (btnEditar) {
            const id = btnEditar.closest('tr').dataset.id;
            const config = await chamarAPI(`/rateio-configs/${id}`); // Busca os dados mais recentes
            abrirModal(config);
        }

        if (btnExcluir) {
            configParaExcluirId = btnExcluir.closest('tr').dataset.id;
            document.getElementById('confirmacaoModalBody').textContent = 'Tem certeza que deseja excluir esta configuração? Esta ação não pode ser desfeita.';
            confirmacaoModal.show();
        }
    });

    // Confirmação de exclusão
    document.getElementById('btnConfirmarExclusao').addEventListener('click', async () => {
        if (!configParaExcluirId) return;
        try {
            await chamarAPI(`/rateio-configs/${configParaExcluirId}`, 'DELETE');
            exibirAlerta('Configuração excluída com sucesso!', 'success');
            carregarConfiguracoes();
        } catch (error) {
            exibirAlerta(`Erro ao excluir: ${error.message}`, 'danger');
        } finally {
            confirmacaoModal.hide();
            configParaExcluirId = null;
        }
    });

    // Carregamento inicial
    carregarConfiguracoes();
});
