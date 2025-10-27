/* global Chart, chamarAPI, verificarAutenticacao, verificarPermissaoAdmin, getUsuarioLogado */

(function () {
    let graficoStatus;
    let graficoTipos;
    let graficoUrgencia;

    async function inicializar() {
        const autenticado = await verificarAutenticacao();
        if (!autenticado) return;
        const admin = await verificarPermissaoAdmin();
        if (!admin) return;
        atualizarNomeUsuario();
        await carregarIndicadores();
    }

    function atualizarNomeUsuario() {
        const usuario = getUsuarioLogado();
        if (usuario) {
            const span = document.getElementById('userName');
            if (span) {
                span.textContent = usuario.nome;
            }
        }
    }

    async function carregarIndicadores() {
        try {
            const dados = await chamarAPI('/suporte_ti/admin/indicadores');
            atualizarCards(dados);
            montarGraficos(dados);
        } catch (error) {
            console.error(error);
        }
    }

    function atualizarCards(dados) {
        const total = dados?.total_chamados || 0;
        const porStatus = dados?.por_status || [];
        const abertos = somarStatus(porStatus, ['Aberto', 'Em Atendimento']);
        const fechados = somarStatus(porStatus, ['Finalizado', 'Cancelado']);

        const indicadorTotal = document.getElementById('indicadorTotal');
        const indicadorAbertos = document.getElementById('indicadorAbertos');
        const indicadorFechados = document.getElementById('indicadorFechados');

        if (indicadorTotal) indicadorTotal.textContent = total;
        if (indicadorAbertos) indicadorAbertos.textContent = abertos;
        if (indicadorFechados) indicadorFechados.textContent = fechados;
    }

    function somarStatus(lista, chaves) {
        const conjunto = new Set(chaves.map((c) => c.toLowerCase()));
        return lista
            .filter((item) => conjunto.has((item.status || '').toLowerCase()))
            .reduce((acc, item) => acc + (item.quantidade || 0), 0);
    }

    function montarGraficos(dados) {
        const coresStatus = ['#0d6efd', '#ffc107', '#198754', '#6c757d', '#6610f2'];
        const coresTipos = ['#6f42c1', '#198754', '#0dcaf0', '#fd7e14', '#d63384', '#20c997'];
        const coresUrgencia = ['#198754', '#ffc107', '#dc3545'];

        const ctxStatus = document.getElementById('graficoStatus');
        const ctxTipos = document.getElementById('graficoTipos');
        const ctxUrgencia = document.getElementById('graficoUrgencia');

        const dadosStatus = dados?.por_status || [];
        const dadosTipos = dados?.por_tipo_equipamento || [];
        const dadosUrgencia = dados?.por_nivel_urgencia || [];

        if (graficoStatus) graficoStatus.destroy();
        if (ctxStatus) {
            graficoStatus = new Chart(ctxStatus, {
                type: 'doughnut',
                data: {
                    labels: dadosStatus.map((item) => item.status),
                    datasets: [
                        {
                            data: dadosStatus.map((item) => item.quantidade),
                            backgroundColor: coresStatus.slice(0, dadosStatus.length),
                        },
                    ],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom' },
                    },
                },
            });
        }

        if (graficoTipos) graficoTipos.destroy();
        if (ctxTipos) {
            graficoTipos = new Chart(ctxTipos, {
                type: 'bar',
                data: {
                    labels: dadosTipos.map((item) => item.tipo),
                    datasets: [
                        {
                            data: dadosTipos.map((item) => item.quantidade),
                            backgroundColor: coresTipos.slice(0, dadosTipos.length),
                        },
                    ],
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0,
                            },
                        },
                    },
                },
            });
        }

        if (graficoUrgencia) graficoUrgencia.destroy();
        if (ctxUrgencia) {
            graficoUrgencia = new Chart(ctxUrgencia, {
                type: 'bar',
                data: {
                    labels: dadosUrgencia.map((item) => item.nivel),
                    datasets: [
                        {
                            label: 'Chamados',
                            data: dadosUrgencia.map((item) => item.quantidade),
                            backgroundColor: coresUrgencia.slice(0, dadosUrgencia.length),
                        },
                    ],
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 },
                        },
                    },
                    plugins: {
                        legend: { display: false },
                    },
                },
            });
        }
    }

    document.addEventListener('DOMContentLoaded', inicializar);
})();
