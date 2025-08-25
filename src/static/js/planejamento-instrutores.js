// Utilizar as mesmas funções/fluxo de dados da página trimestral:
// - Reaproveitar os mesmos filtros de data (ou ler do querystring as mesmas chaves).
// - Chamar a mesma API usada na trimestral (ex.: chamarAPI(urlComParametros, 'GET')).
// - Estruturar dados por instrutor e por dia do mês.

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const intervalo = obterIntervaloUsadoNaTrimestral();
    const itens = await carregarItensPlanejamento(intervalo);

    const { dias, instrutores, mapa } = montarMapaPorInstrutor(itens);

    renderTabelaPorInstrutor(dias, instrutores, mapa);
  } catch (e) {
    console.error(e);
    alert('Falha ao carregar planejamento por instrutor.');
  }
});

// 1) Busca de dados (reutilizando o que já existe na trimestral)
async function carregarItensPlanejamento(intervalo) {
  const url = construirURLDePlanejamento(intervalo);
  const resp = await chamarAPI(url, 'GET');
  return resp?.items || resp || [];
}

function obterIntervaloUsadoNaTrimestral() {
  const params = new URLSearchParams(window.location.search);
  let inicio = params.get('inicio');
  let fim = params.get('fim');

  if (!inicio || !fim) {
    const hoje = new Date();
    const ano = hoje.getFullYear();
    const mes = hoje.getMonth();
    const primeiro = new Date(ano, mes, 1);
    const ultimo = new Date(ano, mes + 1, 0);
    inicio = primeiro.toISOString().slice(0, 10);
    fim = ultimo.toISOString().slice(0, 10);
  }

  return { inicio, fim };
}

function construirURLDePlanejamento(intervalo) {
  const params = new URLSearchParams();
  if (intervalo?.inicio) params.set('inicio', intervalo.inicio);
  if (intervalo?.fim) params.set('fim', intervalo.fim);
  const qs = params.toString();
  return `/planejamento/itens${qs ? `?${qs}` : ''}`;
}

// 2) Mapeamento: dia -> instrutor -> lista de itens (que colidem com o dia)
function montarMapaPorInstrutor(itens) {
  const diasSet = new Set();
  const instrutoresSet = new Set();
  const mapa = {};

  for (const it of itens) {
    const di = new Date(it.data_inicio || it.data);
    const df = new Date(it.data_fim || it.data_final || it.data);

    const instr = (it.instrutor_nome || it.instrutor || it.responsavel || '').trim();
    if (!instr) continue;

    instrutoresSet.add(instr);

    const cursor = new Date(di);
    while (cursor <= df) {
      const iso = cursor.toISOString().slice(0, 10);
      diasSet.add(iso);
      mapa[iso] = mapa[iso] || {};
      mapa[iso][instr] = mapa[iso][instr] || { manha: [], tarde: [] };

      let turno = (it.turno || '').toString().toLowerCase();
      if (!turno) {
        const h = parseInt(String(it.hora_inicio || it.inicio_hora || '0').slice(0, 2), 10);
        turno = h < 12 ? 'manha' : 'tarde';
      } else if (turno.startsWith('m')) {
        turno = 'manha';
      } else {
        turno = 'tarde';
      }

      mapa[iso][instr][turno].push(it);

      cursor.setDate(cursor.getDate() + 1);
    }
  }

  const dias = Array.from(diasSet).sort();
  const instrutores = Array.from(instrutoresSet).sort((a, b) => a.localeCompare(b, 'pt-BR'));

  return { dias, instrutores, mapa };
}

// 3) Renderização da tabela
function renderTabelaPorInstrutor(dias, instrutores, mapa) {
  const thead = document.querySelector('#tabela-por-instrutor thead');
  const tbody = document.querySelector('#tabela-por-instrutor tbody');

  const trHead = document.createElement('tr');
  ['DATA', 'SEMANA', 'TURNO', ...instrutores].forEach(t => {
    const th = document.createElement('th');
    th.textContent = t;
    trHead.appendChild(th);
  });
  thead.innerHTML = '';
  thead.appendChild(trHead);

  const frag = document.createDocumentFragment();
  for (const diaISO of dias) {
    const trManha = document.createElement('tr');
    const trTarde = document.createElement('tr');

    const thData = document.createElement('th');
    thData.textContent = formatarDataCompleta(diaISO);
    thData.setAttribute('rowspan', '2');
    thData.classList.add('dia-col');

    const thSemana = document.createElement('th');
    thSemana.textContent = diaDaSemanaPtBR(diaISO);
    thSemana.setAttribute('rowspan', '2');

    const tdTurnoManha = document.createElement('td');
    tdTurnoManha.textContent = 'Manhã';
    const tdTurnoTarde = document.createElement('td');
    tdTurnoTarde.textContent = 'Tarde';

    for (const nome of instrutores) {
      const tdM = document.createElement('td');
      const tdT = document.createElement('td');

      const atividadesM = mapa[diaISO]?.[nome]?.manha || [];
      const atividadesT = mapa[diaISO]?.[nome]?.tarde || [];

      preencherTdComAtividades(tdM, atividadesM);
      preencherTdComAtividades(tdT, atividadesT);

      trManha.appendChild(tdM);
      trTarde.appendChild(tdT);
    }

    trManha.prepend(tdTurnoManha);
    trManha.prepend(thSemana);
    trManha.prepend(thData);
    trTarde.prepend(tdTurnoTarde);

    frag.appendChild(trManha);
    frag.appendChild(trTarde);
  }

  tbody.innerHTML = '';
  tbody.appendChild(frag);
}

function preencherTdComAtividades(td, atividades) {
  for (const it of atividades) {
    const div = document.createElement('div');
    div.className = 'cell-treinamento';

    const titulo = it.treinamento || it.titulo || it.nome || 'Treinamento';
    const horario = montarFaixaHorario(it);
    const local = it.local || it.sala || '';

    div.textContent = local ? `${titulo} (${horario}) • ${local}` : `${titulo} (${horario})`;
    if (div.textContent.toUpperCase().includes('BLOQUEIO')) {
      div.classList.add('bg-success-subtle');
    }
    td.appendChild(div);
  }
}

function montarFaixaHorario(it) {
  const hi = (it.hora_inicio || it.inicio_hora || '').toString().slice(0, 5);
  const hf = (it.hora_fim || it.fim_hora || '').toString().slice(0, 5);
  return hi && hf ? `${hi}–${hf}` : (hi || hf || '');
}

function formatarDataCompleta(isoDateStr) {
  const d = new Date(isoDateStr);
  const dia = String(d.getDate()).padStart(2, '0');
  const mes = String(d.getMonth() + 1).padStart(2, '0');
  const ano = d.getFullYear();
  return `${dia}/${mes}/${ano}`;
}

function diaDaSemanaPtBR(isoDateStr) {
  const d = new Date(isoDateStr);
  return d.toLocaleDateString('pt-BR', { weekday: 'long' }).replace(/^\w/, c => c.toUpperCase());
}

