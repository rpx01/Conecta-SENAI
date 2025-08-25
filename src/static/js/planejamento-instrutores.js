// Utilizar as mesmas funções/fluxo de dados da página trimestral:
// - Reaproveitar os mesmos filtros de data (ou ler do querystring as mesmas chaves).
// - Chamar a mesma API usada na trimestral (ex.: chamarAPI(urlComParametros, 'GET')).
// - Estruturar dados por instrutor e por dia do mês.

document.addEventListener('DOMContentLoaded', async () => {
  try {
    const intervalo = obterIntervaloUsadoNaTrimestral();
    const itens = await carregarItensPlanejamento(intervalo);

    const { diasDoMes, instrutores, mapa } = montarMapaPorInstrutor(itens, intervalo);

    renderTabelaPorInstrutor(diasDoMes, instrutores, mapa);
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
function montarMapaPorInstrutor(itens, intervalo) {
  const inicio = new Date(intervalo.inicio);
  const ano = inicio.getFullYear();
  const mes = inicio.getMonth();

  const ultimoDia = new Date(ano, mes + 1, 0).getDate();
  const diasDoMes = Array.from({ length: ultimoDia }, (_, i) => i + 1);

  const instrutores = Array.from(new Set(
    itens.map(i => (i.instrutor_nome || i.instrutor || i.responsavel || '').trim()).filter(Boolean)
  )).sort((a, b) => a.localeCompare(b, 'pt-BR'));

  const mapa = {};
  for (const d of diasDoMes) mapa[d] = Object.fromEntries(instrutores.map(n => [n, []]));

  for (const it of itens) {
    const di = new Date(it.data_inicio || it.data);
    const df = new Date(it.data_fim || it.data_final || it.data);

    const cursor = new Date(Math.max(di, new Date(ano, mes, 1)));
    const limite = new Date(Math.min(df, new Date(ano, mes, ultimoDia)));

    const instr = (it.instrutor_nome || it.instrutor || it.responsavel || '').trim();
    if (!instr) continue;

    while (cursor <= limite) {
      const d = cursor.getDate();
      mapa[d][instr].push(it);
      cursor.setDate(cursor.getDate() + 1);
    }
  }

  return { diasDoMes, instrutores, mapa };
}

// 3) Renderização da tabela
function renderTabelaPorInstrutor(diasDoMes, instrutores, mapa) {
  const thead = document.querySelector('#tabela-por-instrutor thead');
  const tbody = document.querySelector('#tabela-por-instrutor tbody');

  const trHead = document.createElement('tr');
  const thDia = document.createElement('th');
  thDia.textContent = 'Dia';
  thDia.classList.add('dia-col');
  trHead.appendChild(thDia);

  for (const nome of instrutores) {
    const th = document.createElement('th');
    th.textContent = nome;
    trHead.appendChild(th);
  }
  thead.innerHTML = '';
  thead.appendChild(trHead);

  const frag = document.createDocumentFragment();
  for (const d of diasDoMes) {
    const tr = document.createElement('tr');

    const th = document.createElement('th');
    th.classList.add('dia-col');
    th.textContent = String(d).padStart(2, '0');
    tr.appendChild(th);

    for (const nome of instrutores) {
      const td = document.createElement('td');
      const itensDoDia = mapa[d][nome] || [];
      for (const it of itensDoDia) {
        const div = document.createElement('div');
        div.className = 'cell-treinamento';

        const titulo = it.treinamento || it.titulo || it.nome || 'Treinamento';
        const horario = montarFaixaHorario(it);
        const local = it.local || it.sala || '';

        div.textContent = local ? `${titulo} (${horario}) • ${local}` : `${titulo} (${horario})`;
        td.appendChild(div);
      }
      tr.appendChild(td);
    }

    frag.appendChild(tr);
  }

  tbody.innerHTML = '';
  tbody.appendChild(frag);
}

function montarFaixaHorario(it) {
  const hi = (it.hora_inicio || it.inicio_hora || '').toString().slice(0, 5);
  const hf = (it.hora_fim || it.fim_hora || '').toString().slice(0, 5);
  return hi && hf ? `${hi}–${hf}` : (hi || hf || '');
}

