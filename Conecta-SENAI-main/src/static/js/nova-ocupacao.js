// Funções para nova ocupação

// Variáveis globais
let salasDisponiveis = [];
let turmasDisponiveis = [];
let instrutoresDisponiveis = [];
let tiposOcupacaoData = [];
let ocupacaoEditando = null;
let disponibilidadeAtual = null;

// Converte o retorno de erros da API em uma mensagem legível
function formatarErros(erro) {
    if (Array.isArray(erro)) {
        return erro.map(e => {
            if (e.loc && e.msg) {
                return `${e.loc.join(' \u2192 ')}: ${e.msg}`;
            }
            return JSON.stringify(e);
        }).join('; ');
    }
    return erro;
}

// Retorna o turno baseado nos horários
function obterTurnoPorHorario(inicio, fim) {
    const mapa = {
        '08:00': 'Manhã',
        '13:30': 'Tarde',
        '18:30': 'Noite'
    };
    if (mapa[inicio]) {
        return mapa[inicio];
    }
    // fallback
    if (inicio < '12:00') return 'Manhã';
    if (inicio < '18:30') return 'Tarde';
    return 'Noite';
}

// Carrega tipos de ocupação
async function carregarTiposOcupacao() {
    try {
        const response = await fetch(`${API_URL}/ocupacoes/tipos`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        
        if (response.ok) {
            tiposOcupacaoData = await response.json();
            
            const select = document.getElementById('tipoOcupacao');
            select.innerHTML = '<option value="">Selecione...</option>';
            
            tiposOcupacaoData.forEach(tipo => {
                select.innerHTML += `<option value="${tipo.valor}">${tipo.nome}</option>`;
            });
        }
    } catch (error) {
        console.error('Erro ao carregar tipos de ocupação:', error);
    }
}

// Carrega salas disponíveis
async function carregarSalas() {
    try {
        const response = await fetch(`${API_URL}/salas?status=ativa`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        
        if (response.ok) {
            salasDisponiveis = await response.json();
            
            const select = document.getElementById('salaOcupacao');
            select.innerHTML = '<option value="">Selecione...</option>';
            
            salasDisponiveis.forEach(sala => {
                select.innerHTML += `<option value="${sala.id}">${sala.nome} (${sala.capacidade} pessoas)</option>`;
            });
        }
    } catch (error) {
        console.error('Erro ao carregar salas:', error);
    }
}

// Carrega instrutores disponíveis
async function carregarInstrutores() {
    try {
        const response = await fetch(`${API_URL}/instrutores?status=ativo`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        
        if (response.ok) {
            instrutoresDisponiveis = await response.json();
            
            const select = document.getElementById('instrutorOcupacao');
            select.innerHTML = '<option value="">Nenhum instrutor</option>';
            
            instrutoresDisponiveis.forEach(instrutor => {
                select.innerHTML += `<option value="${instrutor.id}">${instrutor.nome}</option>`;
            });
        }
    } catch (error) {
        console.error('Erro ao carregar instrutores:', error);
    }
}


async function carregarTurmasSelect() {
    try {
        const response = await fetch(`${API_URL}/turmas`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        if (response.ok) {
            turmasDisponiveis = await response.json();
            const select = document.getElementById('cursoEvento');
            select.innerHTML = '<option value="">Selecione...</option>';
            turmasDisponiveis.forEach(t => {
                select.innerHTML += `<option value="${t.nome}">${t.nome}</option>`;
            });
        }
    } catch (error) {
        console.error('Erro ao carregar turmas:', error);
    }
}

// Adiciona listeners de validação
function adicionarListenersValidacao() {
    document.getElementById('dataInicio').addEventListener('change', validarDatas);
    document.getElementById('dataFim').addEventListener('change', validarDatas);
    document.getElementById('dataInicio').addEventListener('change', verificarDisponibilidade);
    document.getElementById('dataFim').addEventListener('change', verificarDisponibilidade);
    document.getElementById('turno').addEventListener('change', verificarDisponibilidade);
    document.getElementById('salaOcupacao').addEventListener('change', verificarDisponibilidade);

    // Verifica se há parâmetros na URL
    verificarParametrosURL();
}

// Verifica parâmetros da URL
function verificarParametrosURL() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Data pré-selecionada
    const data = urlParams.get('data');
    if (data) {
        document.getElementById('dataInicio').value = data;
        document.getElementById('dataFim').value = data;
    }
    
    // Edição de ocupação
    const editarId = urlParams.get('editar');
    if (editarId) {
        carregarOcupacaoParaEdicao(editarId);
    }

    verificarDisponibilidade();
}

// Carrega ocupação para edição
async function carregarOcupacaoParaEdicao(id) {
    try {
        const response = await fetch(`${API_URL}/ocupacoes/${id}`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        
        if (response.ok) {
            ocupacaoEditando = await response.json();
            
            // Preenche o formulário
            document.getElementById('cursoEvento').value = ocupacaoEditando.curso_evento;
            document.getElementById('tipoOcupacao').value = ocupacaoEditando.tipo_ocupacao;
            document.getElementById('dataInicio').value = ocupacaoEditando.data_inicio || ocupacaoEditando.data;
            document.getElementById('dataFim').value = ocupacaoEditando.data_fim || ocupacaoEditando.data;
            document.getElementById('turno').value = obterTurnoPorHorario(ocupacaoEditando.horario_inicio, ocupacaoEditando.horario_fim);
            document.getElementById('salaOcupacao').value = ocupacaoEditando.sala_id;
            document.getElementById('instrutorOcupacao').value = ocupacaoEditando.instrutor_id || '';
            document.getElementById('observacoesOcupacao').value = ocupacaoEditando.observacoes || '';

            // Atualiza título
            document.querySelector('h1').textContent = 'Editar Ocupação';
            verificarDisponibilidade();
        } else {
            throw new Error('Erro ao carregar ocupação');
        }
    } catch (error) {
        console.error('Erro ao carregar ocupação para edição:', error);
        exibirAlerta('Erro ao carregar dados da ocupação.', 'danger');
    }
}

// Valida datas de início e fim
function validarDatas() {
    const inicio = document.getElementById('dataInicio').value;
    const fim = document.getElementById('dataFim').value;
    if (inicio && fim && fim < inicio) {
        document.getElementById('dataFim').setCustomValidity('Data de fim deve ser posterior ou igual à data de início');
    } else {
        document.getElementById('dataFim').setCustomValidity('');
    }

    document.getElementById('dataInicio').setCustomValidity('');
}

// Verifica disponibilidade de forma dinâmica
async function verificarDisponibilidade() {
    const salaId = document.getElementById('salaOcupacao').value;
    const dataInicio = document.getElementById('dataInicio').value;
    const dataFim = document.getElementById('dataFim').value;
    const turno = document.getElementById('turno').value;

    const statusEl = document.getElementById('statusDisponibilidade');

    disponibilidadeAtual = null;

    if (!salaId || !dataInicio || !dataFim || !turno) {
        statusEl.textContent = '';
        statusEl.className = '';
        return;
    }

    try {
        const params = new URLSearchParams({
            sala_id: salaId,
            data_inicio: dataInicio,
            data_fim: dataFim,
            turno: turno
        });

        if (ocupacaoEditando) {
            params.append('ocupacao_id', ocupacaoEditando.id);
        }

        const response = await fetch(`${API_URL}/ocupacoes/verificar-disponibilidade?${params.toString()}`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        const resultado = await response.json();

        if (response.ok) {
            disponibilidadeAtual = resultado.disponivel;
            if (resultado.disponivel) {
                statusEl.textContent = '✅ Período disponível para agendamento.';
                statusEl.className = 'text-success';
            } else {
                statusEl.textContent = '❌ Período indisponível: Já existe outra ocupação para esta sala e turno.';
                statusEl.className = 'text-danger';
            }
        } else {
            throw new Error(formatarErros(resultado.erro) || 'Erro ao verificar disponibilidade');
        }
    } catch (error) {
        statusEl.textContent = error.message;
        statusEl.className = 'text-danger';
        disponibilidadeAtual = false;
        console.error('Erro ao verificar disponibilidade:', error);
    }
}

// Salva a ocupação
async function salvarOcupacao() {
    
    try {
        const formData = {
            curso_evento: document.getElementById('cursoEvento').value,
            tipo_ocupacao: document.getElementById('tipoOcupacao').value,
            data_inicio: document.getElementById('dataInicio').value,
            data_fim: document.getElementById('dataFim').value,
            turno: document.getElementById('turno').value,
            sala_id: parseInt(document.getElementById('salaOcupacao').value),
            observacoes: document.getElementById('observacoesOcupacao').value
        };
        
        const instrutorId = document.getElementById('instrutorOcupacao').value;
        if (instrutorId) {
            formData.instrutor_id = parseInt(instrutorId);
        }
        
        const urlParams = new URLSearchParams(window.location.search);
        const editarId = urlParams.get('editar');
        const isEdicao = editarId !== null;
        const url = isEdicao ? `${API_URL}/ocupacoes/${editarId}` : `${API_URL}/ocupacoes`;
        const method = isEdicao ? 'PUT' : 'POST';
        
        await verificarDisponibilidade();
        if (disponibilidadeAtual === false) {
            throw new Error('Ocupação não pode ser salva. Conflito com outra ocupação existente.');
        }

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify(formData)
        });
        
        const resultado = await response.json();
        
        if (response.ok) {
            exibirAlerta('Ocupação salva com sucesso.', 'success');
            window.location.href = '/calendario-salas.html';
        } else {
            throw new Error(formatarErros(resultado.erro) || 'Erro ao salvar ocupação');
        }
    } catch (error) {
        console.error('Erro ao salvar ocupação:', error);
        exibirAlerta(error.message, 'danger');
    }
}

// Valida formulário
function validarFormulario() {
    const campos = [
        'cursoEvento',
        'tipoOcupacao',
        'dataInicio',
        'dataFim',
        'turno',
        'salaOcupacao'
    ];
    
    let valido = true;
    
    campos.forEach(campo => {
        const elemento = document.getElementById(campo);
        if (!elemento.value.trim()) {
            elemento.classList.add('is-invalid');
            valido = false;
        } else {
            elemento.classList.remove('is-invalid');
        }
    });
    
    // Valida datas
    validarDatas();

    if (document.getElementById('dataInicio').validationMessage || document.getElementById('dataFim').validationMessage) {
        valido = false;
    }
    
    if (!valido) {
        exibirAlerta('Por favor, preencha todos os campos obrigatórios corretamente.', 'warning');
    }
    
    return valido;
}

// Avança para próximo passo

// Função para exibir alertas
function exibirAlerta(mensagem, tipo) {
    // Remove alertas existentes
    const alertasExistentes = document.querySelectorAll('.alert-auto-dismiss');
    alertasExistentes.forEach(alerta => alerta.remove());

    // Cria novo alerta
    const alerta = document.createElement('div');
    alerta.className = `alert alert-${tipo} alert-dismissible fade show alert-auto-dismiss`;
    alerta.textContent = mensagem;
    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'btn-close';
    closeBtn.setAttribute('data-bs-dismiss', 'alert');
    closeBtn.setAttribute('aria-label', 'Close');
    alerta.appendChild(closeBtn);
    
    // Insere no início do main
    const main = document.querySelector('main');
    main.insertBefore(alerta, main.firstChild);
    
    // Remove automaticamente após 5 segundos
    setTimeout(() => {
        if (alerta.parentNode) {
            alerta.remove();
        }
    }, 5000);
}

// Exibe aviso quando "Aula Regular" é selecionada
function monitorarSelecaoAulaRegular() {
    const tipoOcupacaoSelect = document.getElementById('tipoOcupacao');
    const dataInicioInput = document.getElementById('dataInicio');
    const dataFimInput = document.getElementById('dataFim');

    const avisoDiv = document.createElement('div');
    avisoDiv.className = 'form-text text-muted mt-2';
    avisoDiv.id = 'aviso-fim-de-semana';
    dataFimInput.parentNode.appendChild(avisoDiv);

    const verificarAviso = () => {
        if (tipoOcupacaoSelect.value === 'aula_regular') {
            avisoDiv.innerHTML = '<i class="bi bi-info-circle"></i> Lembrete: Sábados e domingos serão ignorados para agendamentos de Aulas Regulares.';
            avisoDiv.style.display = 'block';
        } else {
            avisoDiv.style.display = 'none';
        }
    };

    tipoOcupacaoSelect.addEventListener('change', verificarAviso);
    verificarAviso();
}

// Garante envio correto do formulário em modo de edição ou criação
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('formNovaOcupacao');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await salvarOcupacao();
        });
    }

    // Inicia monitoramento para avisos de "Aula Regular"
    monitorarSelecaoAulaRegular();
});

