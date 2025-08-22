/* global chamarAPI, executarAcaoComFeedback */

// Utilitário: obtém o primeiro e o último dia (ISO) do mês escolhido
function limitesDoMes(ano, mes1a12) {
  const primeiro = new Date(ano, mes1a12 - 1, 1);
  const ultimo = new Date(ano, mes1a12, 0);
  const pad2 = n => String(n).padStart(2, '0');
  const inicioISO = `${primeiro.getFullYear()}-${pad2(primeiro.getMonth()+1)}-${pad2(primeiro.getDate())}`;
  const fimISO    = `${ultimo.getFullYear()}-${pad2(ultimo.getMonth()+1)}-${pad2(ultimo.getDate())}`;
  return { primeiro, ultimo, inicioISO, fimISO };
}

function diasDoMes(date) {
  const dias = [];
  const ano = date.getFullYear();
  const mes = date.getMonth(); // 0..11
  const ultimo = new Date(ano, mes + 1, 0).getDate();
  for (let d = 1; d <= ultimo; d++) dias.push(new Date(ano, mes, d));
  return dias;
}

function ehFimDeSemana(date) {
  const dow = date.getDay(); // 0 dom, 6 sáb
  return dow === 0 || dow === 6;
}

/**
 * Transforma a lista "plana" de itens em um índice por instrutor e dia do mês.
 * IMPORTANTE: Reutilize os MESMOS campos já usados em /planejamento-trimestral.html.
 * Ajuste abaixo os nomes das propriedades de acordo com a estrutura atual.
 */
function pivotPorInstrutor(itens) {
  // Adapte estes nomes aos campos que a página trimestral já usa
  const getInstrutor = (it) => it.instrutor_nome ?? it.instrutor ?? 'Sem instrutor';
  const getTitulo    = (it) => it.curso_evento ?? it.treinamento ?? it.titulo ?? it.nome ?? '(sem título)';
  const getIni       = (it) => new Date(it.data_inicio ?? it.inicio ?? it.data ?? it.dataInicial);
  const getFim       = (it) => new Date(it.data_fim ?? it.fim ?? it.termino ?? it.dataFinal ?? getIni(it));

  const dados = new Map(); // Map<instrutor, Map<diaNumero, string[]>>
  const instrutores = new Set();

  for (const it of itens) {
    const instr = getInstrutor(it);
    instrutores.add(instr);

    const ini = getIni(it);
    const fim = getFim(it);
    // Percorre todos os dias cobertos pelo treinamento
    for (let d = new Date(ini); d <= fim; d.setDate(d.getDate() + 1)) {
      const diaNum = d.getDate();
      if (!dados.has(instr)) dados.set(instr, new Map());
      if (!dados.get(instr).has(diaNum)) dados.get(instr).set(diaNum, []);
      dados.get(instr).get(diaNum).push(getTitulo(it));
    }
  }
  return { dados, instrutores: Array.from(instrutores).sort((a,b)=>a.localeCompare(b, 'pt-BR')) };
}

function desenharTabela(dias, instrutores, dados) {
  const head = document.getElementById('gridHead');
  const body = document.getElementById('gridBody');
  head.innerHTML = ''; body.innerHTML = '';

  // Cabeçalho
  const trHead = document.createElement('tr');
  const thDia = document.createElement('th'); thDia.textContent = 'Dia';
  trHead.appendChild(thDia);
  for (const inst of instrutores) {
    const th = document.createElement('th');
    th.textContent = inst;
    trHead.appendChild(th);
  }
  head.appendChild(trHead);

  // Linhas do mês
  for (const dt of dias) {
    const tr = document.createElement('tr');
    if (ehFimDeSemana(dt)) tr.classList.add('fim-de-semana');

    const tdDia = document.createElement('td');
    tdDia.textContent = dt.getDate();
    tr.appendChild(tdDia);

    for (const inst of instrutores) {
      const td = document.createElement('td');
      const porInstrutor = dados.get(inst);
      const lista = porInstrutor?.get(dt.getDate()) ?? [];
      for (const nome of lista) {
        const tag = document.createElement('span');
        tag.className = 'badge-treinamento';
        tag.textContent = nome;
        td.appendChild(tag);
      }
      tr.appendChild(td);
    }
    body.appendChild(tr);
  }
}

async function carregar() {
  // Define mês inicial no input se vazio
  const input = document.getElementById('mesRef');
  if (!input.value) {
    const hoje = new Date();
    input.value = `${hoje.getFullYear()}-${String(hoje.getMonth()+1).padStart(2,'0')}`;
  }

  const [ano, mes] = input.value.split('-').map(Number);
  const { primeiro, inicioISO, fimISO } = limitesDoMes(ano, mes);

  // Use a mesma URL de consulta da página trimestral
  const url = `/ocupacoes?data_inicio=${inicioISO}&data_fim=${fimISO}`; // ajuste se necessário

  const itens = await chamarAPI(url, 'GET'); // utilitário já existente no projeto
  const { dados, instrutores } = pivotPorInstrutor(itens);
  const dias = diasDoMes(primeiro);
  desenharTabela(dias, instrutores, dados);
}

document.getElementById('btnRecarregar').addEventListener('click', (e) => {
  executarAcaoComFeedback(e.currentTarget, carregar); // utilitário padrão do projeto
});

document.addEventListener('DOMContentLoaded', carregar);

