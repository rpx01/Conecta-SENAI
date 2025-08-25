// Utilizar as mesmas funções/fluxo de dados da página trimestral:
// - Reaproveitar os mesmos filtros de data (ou ler do querystring as mesmas chaves).
// - Chamar a mesma API usada na trimestral (ex.: chamarAPI(urlComParametros, 'GET')).
// - Estruturar dados por instrutor e por dia do mês.


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

// === helpers novos ===
function formatarDiaCompleto(ano, mesZeroBased, dia) {
  const dt = new Date(ano, mesZeroBased, dia);
  return dt.toLocaleDateString('pt-BR');
}

function nomeDaSemana(ano, mesZeroBased, dia) {
  const dt = new Date(ano, mesZeroBased, dia);
  const w = dt.toLocaleDateString('pt-BR', { weekday: 'long' });
  return w.charAt(0).toUpperCase() + w.slice(1);
}

function horaParaMinutos(hhmm) {
  if (!hhmm || typeof hhmm !== 'string' || !hhmm.includes(':')) return null;
  const [h, m] = hhmm.split(':').map((x) => parseInt(x, 10));
  if (Number.isNaN(h) || Number.isNaN(m)) return null;
  return h * 60 + m;
}

function classificarTurno(item) {
  const hi = (item.hora_inicio || item.inicio_hora || '').slice(0, 5);
  const hf = (item.hora_fim || item.fim_hora || '').slice(0, 5);

  const ini = horaParaMinutos(hi);
  const fim = horaParaMinutos(hf);
  const meioDia = 12 * 60;

  if (ini == null || fim == null) return 'Ambos';
  if (ini < meioDia && fim <= meioDia) return 'Manhã';
  if (ini >= meioDia) return 'Tarde';
  return 'Ambos';
}

// === ATUALIZE a função que monta o mapa para também devolver ano/mes ===
function montarMapaPorInstrutor(itens, intervalo) {
  const inicio = new Date(intervalo.inicio);
  const ano = inicio.getFullYear();
  const mes = inicio.getMonth();

  const ultimoDia = new Date(ano, mes + 1, 0).getDate();
  const diasDoMes = Array.from({ length: ultimoDia }, (_, i) => i + 1);

  const instrutores = Array.from(
    new Set(
      itens
        .map((i) => (i.instrutor_nome || i.instrutor || i.responsavel || '').trim())
        .filter(Boolean)
    )
  ).sort((a, b) => a.localeCompare(b, 'pt-BR'));

  const mapa = {};
  for (const d of diasDoMes) mapa[d] = Object.fromEntries(instrutores.map((n) => [n, []]));

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

  return { diasDoMes, instrutores, mapa, ano, mes };
}

// === SUBSTITUA o renderer para gerar Dia + Semana + Turno e duas linhas por dia ===
function renderTabelaPorInstrutor(diasDoMes, instrutores, mapa, contextoMes) {
  const { ano, mes } = contextoMes;
  const thead = document.querySelector('#tabela-por-instrutor thead');
  const tbody = document.querySelector('#tabela-por-instrutor tbody');

  const trHead = document.createElement('tr');

  const thDia = document.createElement('th');
  thDia.textContent = 'DATA';
  thDia.classList.add('dia-col');
  trHead.appendChild(thDia);

  const thSemana = document.createElement('th');
  thSemana.textContent = 'SEMANA';
  trHead.appendChild(thSemana);

  const thTurno = document.createElement('th');
  thTurno.textContent = 'TURNO';
  trHead.appendChild(thTurno);

  for (const nome of instrutores) {
    const th = document.createElement('th');
    th.textContent = nome;
    trHead.appendChild(th);
  }

  thead.innerHTML = '';
  thead.appendChild(trHead);

  const frag = document.createDocumentFragment();
  const turnos = ['Manhã', 'Tarde'];

  for (const d of diasDoMes) {
    for (const turno of turnos) {
      const tr = document.createElement('tr');

      const tdData = document.createElement('th');
      tdData.classList.add('dia-col');
      tdData.textContent = formatarDiaCompleto(ano, mes, d);
      tr.appendChild(tdData);

      const tdSemana = document.createElement('td');
      tdSemana.textContent = nomeDaSemana(ano, mes, d);
      tr.appendChild(tdSemana);

      const tdTurno = document.createElement('td');
      tdTurno.textContent = turno;
      tr.appendChild(tdTurno);

      for (const nome of instrutores) {
        const td = document.createElement('td');
        const itensDoDia = (mapa[d] && mapa[d][nome]) || [];

        const itensFiltrados = itensDoDia.filter((it) => {
          const cls = classificarTurno(it);
          return cls === 'Ambos' || cls === turno;
        });

        for (const it of itensFiltrados) {
          const div = document.createElement('div');
          div.className = `cell-treinamento ${getClasseTurno(turno)}`;

          const titulo = it.treinamento || it.titulo || it.nome || 'Treinamento';
          const hi = (it.hora_inicio || it.inicio_hora || '').toString().slice(0, 5);
          const hf = (it.hora_fim || it.fim_hora || '').toString().slice(0, 5);
          const faixa = hi && hf ? `${hi}–${hf}` : (hi || hf || '');
          const local = it.local || it.sala || '';

          div.textContent = local ? `${titulo} (${faixa}) • ${local}` : `${titulo} (${faixa})`;
          td.appendChild(div);
        }

        tr.appendChild(td);
      }

      frag.appendChild(tr);
    }
  }

  tbody.innerHTML = '';
  tbody.appendChild(frag);
}

// === AJUSTE NA INICIALIZAÇÃO: passe ano/mes ao renderer ===
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const intervalo = obterIntervaloUsadoNaTrimestral();
    const itens = await carregarItensPlanejamento(intervalo);
    const { diasDoMes, instrutores, mapa, ano, mes } = montarMapaPorInstrutor(itens, intervalo);
    renderTabelaPorInstrutor(diasDoMes, instrutores, mapa, { ano, mes });
  } catch (e) {
    console.error(e);
    alert('Falha ao carregar planejamento por instrutor.');
  }
});

