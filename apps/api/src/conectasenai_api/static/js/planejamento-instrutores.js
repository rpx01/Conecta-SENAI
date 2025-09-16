// Página de planejamento por instrutor
// Constrói uma tabela com linhas para manhã e tarde de cada dia, preenchendo
// as células de acordo com o turno associado ao horário de cada atividade.

document.addEventListener('DOMContentLoaded', async () => {
  try {
    const intervalo = obterIntervaloUsadoNaTrimestral();
    const itens = await carregarItensPlanejamento(intervalo);

    const diasSet = new Set();
    const instrutoresSet = new Set();

    // Coleta de dias e instrutores existentes
    itens.forEach(it => {
      const di = new Date(it.data_inicio || it.data);
      const df = new Date(it.data_fim || it.data_final || it.data);
      const nomeInstr = (it.instrutor_nome || it.instrutor || it.responsavel || '').trim();
      if (!nomeInstr) return;
      instrutoresSet.add(nomeInstr);
      const cursor = new Date(di);
      while (cursor <= df) {
        diasSet.add(cursor.toISOString().slice(0, 10));
        cursor.setDate(cursor.getDate() + 1);
      }
    });

    const dias = Array.from(diasSet).sort();
    const instrutores = Array.from(instrutoresSet).sort((a, b) => a.localeCompare(b, 'pt-BR'));
    const { diaContainers, instrutorIndexMap } = construirTabela(dias, instrutores);

    // Distribui os itens nas células corretas
    itens.forEach(it => {
      const instr = (it.instrutor_nome || it.instrutor || it.responsavel || '').trim();
      const idx = instrutorIndexMap[instr];
      if (idx === undefined) return;

      const slots = mapTurnoToSlots(it?.horario?.turno);
      const html = `
        <div class="atividade">
          <div>${it.descricao || it.treinamento || ''}</div>
          <small>${it?.horario?.nome || ''}</small>
        </div>
      `;

      const di = new Date(it.data_inicio || it.data);
      const df = new Date(it.data_fim || it.data_final || it.data);
      const cursor = new Date(di);
      while (cursor <= df) {
        const iso = cursor.toISOString().slice(0, 10);
        const cont = diaContainers[iso];
        if (cont) preencherCelulaPorTurno(cont, slots, idx, html);
        cursor.setDate(cursor.getDate() + 1);
      }
    });
  } catch (e) {
    console.error(e);
    alert('Falha ao carregar planejamento por instrutor.');
  }
});

// Util: remover acentos e normalizar
function normalize(str) {
  if (!str) return '';
  return str
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

// Mapeia o turno em slots de linhas
function mapTurnoToSlots(turnoRaw) {
  const t = normalize(turnoRaw);
  if (t.includes('manha') && t.includes('tarde')) return ['manha', 'tarde'];
  if (t.includes('manha')) return ['manha'];
  if (t.includes('tarde')) return ['tarde'];
  return ['manha', 'tarde'];
}

// Preenche uma célula da linha/coluna correta
function preencherCelulaPorTurno(containerTabela, slots, instrutorIndex, htmlConteudo) {
  slots.forEach(slot => {
    const linha = containerTabela.querySelector(`tr.linha-turno[data-turno="${slot}"]`);
    if (!linha) return;
    const celulas = linha.querySelectorAll('.col-conteudo');
    const alvo = celulas[instrutorIndex];
    if (alvo) {
      if (alvo.innerHTML.trim()) {
        alvo.innerHTML += '<hr class="m-0 my-1">';
      }
      alvo.innerHTML += htmlConteudo;
    }
  });
}

// Constrói o cabeçalho e os corpos da tabela
function construirTabela(dias, instrutores) {
  const tabela = document.getElementById('tabela-por-instrutor');
  const thead = tabela.querySelector('thead');

  const trHead = document.createElement('tr');
  ['DATA', 'SEMANA', 'TURNO', ...instrutores].forEach(t => {
    const th = document.createElement('th');
    th.textContent = t;
    trHead.appendChild(th);
  });
  thead.innerHTML = '';
  thead.appendChild(trHead);

  const diaContainers = {};
  const instrutorIndexMap = {};
  instrutores.forEach((n, i) => { instrutorIndexMap[n] = i; });

  dias.forEach(diaISO => {
    const corpo = document.createElement('tbody');
    corpo.dataset.dia = diaISO;

    const trManha = document.createElement('tr');
    trManha.classList.add('linha-turno');
    trManha.dataset.turno = 'manha';

    const trTarde = document.createElement('tr');
    trTarde.classList.add('linha-turno');
    trTarde.dataset.turno = 'tarde';

    const thData = document.createElement('th');
    thData.textContent = formatarDataCompleta(diaISO);
    thData.rowSpan = 2;
    thData.classList.add('dia-col');

    const thSemana = document.createElement('th');
    thSemana.textContent = diaDaSemanaPtBR(diaISO);
    thSemana.rowSpan = 2;

    const tdTurnoM = document.createElement('td');
    tdTurnoM.textContent = 'Manhã';
    const tdTurnoT = document.createElement('td');
    tdTurnoT.textContent = 'Tarde';

    for (let i = 0; i < instrutores.length; i++) {
      const tdM = document.createElement('td');
      tdM.classList.add('col-conteudo', `col-instrutor-${i + 1}`);
      const tdT = document.createElement('td');
      tdT.classList.add('col-conteudo', `col-instrutor-${i + 1}`);
      trManha.appendChild(tdM);
      trTarde.appendChild(tdT);
    }

    trManha.prepend(tdTurnoM);
    trManha.prepend(thSemana);
    trManha.prepend(thData);
    trTarde.prepend(tdTurnoT);

    corpo.appendChild(trManha);
    corpo.appendChild(trTarde);
    tabela.appendChild(corpo);
    diaContainers[diaISO] = corpo;
  });

  return { diaContainers, instrutorIndexMap };
}

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
