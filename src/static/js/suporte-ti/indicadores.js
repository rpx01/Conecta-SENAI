let graficoStatus;
let graficoUrgencia;
let graficoArea;
let graficoEquipamento;

function formatarDuracao(segundos) {
    if (!segundos || segundos <= 0) return '—';
    const minutos = Math.round(segundos / 60);
    if (minutos < 60) {
        return `${minutos} min`;
    }
    const horas = Math.floor(minutos / 60);
    const minutosRestantes = minutos % 60;
    if (horas < 24) {
        return `${horas}h ${minutosRestantes}min`;
    }
    const dias = Math.floor(horas / 24);
    const horasRestantes = horas % 24;
    return `${dias}d ${horasRestantes}h`;
}

function atualizarCards(dados) {
    document.getElementById('totalChamados').textContent = dados.total_chamados ?? 0;
    document.getElementById('mediaResolucao').textContent = formatarDuracao(dados.media_tempo_resolucao_segundos);
    const totalResolvidos = dados.chamados_por_status?.resolvido ?? 0;
    document.getElementById('totalResolvidos').textContent = totalResolvidos;
    const totalCriticos = dados.chamados_por_urgencia?.critica ?? 0;
    document.getElementById('totalCriticos').textContent = totalCriticos;
}

function destruirGrafico(grafico) {
    if (grafico) {
        grafico.destroy();
    }
}

function criarGraficoPizza(ctx, labels, valores, cores) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: valores,
                backgroundColor: cores,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function criarGraficoBarras(ctx, labels, valores, cores) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                data: valores,
                backgroundColor: cores,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 }
                }
            }
        }
    });
}

function atualizarGraficos(dados) {
    const statusLabels = Object.keys(window.__suporteTI.STATUS_LABELS).map(status => window.__suporteTI.STATUS_LABELS[status]);
    const statusValores = Object.keys(window.__suporteTI.STATUS_LABELS).map(status => dados.chamados_por_status?.[status] ?? 0);
    const statusCores = ['#6c757d', '#0dcaf0', '#198754', '#343a40'];

    destruirGrafico(graficoStatus);
    graficoStatus = criarGraficoPizza(document.getElementById('graficoStatus'), statusLabels, statusValores, statusCores);

    const urgenciaLabels = Object.keys(window.__suporteTI.URGENCIA_LABELS).map(u => window.__suporteTI.URGENCIA_LABELS[u]);
    const urgenciaValores = Object.keys(window.__suporteTI.URGENCIA_LABELS).map(u => dados.chamados_por_urgencia?.[u] ?? 0);
    const urgenciaCores = ['#0d6efd', '#fd7e14', '#dc3545', '#6f42c1'];

    destruirGrafico(graficoUrgencia);
    graficoUrgencia = criarGraficoPizza(document.getElementById('graficoUrgencia'), urgenciaLabels, urgenciaValores, urgenciaCores);

    const areas = dados.chamados_por_area || [];
    const areaLabels = areas.map(item => item.nome);
    const areaValores = areas.map(item => item.total);

    destruirGrafico(graficoArea);
    graficoArea = criarGraficoBarras(document.getElementById('graficoArea'), areaLabels, areaValores, '#0d6efd');

    const equipamentos = dados.chamados_por_equipamento || [];
    const equipamentoLabels = equipamentos.map(item => item.nome);
    const equipamentoValores = equipamentos.map(item => item.total);

    destruirGrafico(graficoEquipamento);
    graficoEquipamento = criarGraficoBarras(document.getElementById('graficoEquipamento'), equipamentoLabels, equipamentoValores, '#6610f2');
}

async function carregarIndicadores() {
    try {
        const dados = await chamarAPI('/support/indicadores');
        atualizarCards(dados);
        atualizarGraficos(dados);
    } catch (erro) {
        console.error('Erro ao carregar indicadores', erro);
        showToast('Não foi possível carregar os indicadores do suporte.', 'danger');
    }
}

(async function init() {
    if (!(await verificarPermissaoAdmin())) return;
    await carregarIndicadores();
})();
