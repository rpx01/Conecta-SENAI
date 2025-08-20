function formatarDataBR(iso) {
  if (!iso) return '-';
  const d = new Date(iso);
  return d.toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo' });
}
function nomeDiaSemana(iso) {
  if (!iso) return '-';
  const d = new Date(iso);
  // Ex.: "segunda-feira"
  return d.toLocaleDateString('pt-BR', { weekday: 'long', timeZone: 'America/Sao_Paulo' });
}
function montarHorario(horaInicio, horaFim) {
  const hi = horaInicio ?? '';
  const hf = horaFim ?? '';
  return (hi && hf) ? `${hi} às ${hf}` : '-';
}

function normalizarParaResumo(item) {
  // Os nomes das propriedades devem seguir o que já vem no dataset do Planejamento Trimestral.
  // Use fallback com '-' quando o campo não existir.
  const dataInicio = item.data_inicio || item.data_inicial || item.inicio || item.data || null;
  const dataFim    = item.data_final  || item.termino     || item.fim   || null;

  return {
    dataInicio: formatarDataBR(dataInicio),
    dataFim:    formatarDataBR(dataFim),
    semana:     nomeDiaSemana(dataInicio),
    horario:    montarHorario(item.hora_inicio || item.horario_inicio, item.hora_fim || item.horario_fim),
    carga:      (item.carga_horaria ?? item.ch ?? '-'),
    modalidade: (item.modalidade ?? '-'),
    treinamento:(item.treinamento || item.nome_treinamento || item.titulo || '-'),
    local:      (item.local ?? item.unidade ?? '-'),
    limite:     (item.limite_inscricao ?? item.limite ?? item.vagas ?? '-'),
    link:       (item.link_inscricao || item.link || null)
  };
}

function renderTabelaResumo(listaNormalizada) {
  const tbody = document.querySelector('#tabela-treinamentos-resumo tbody');
  tbody.innerHTML = '';

  for (const r of listaNormalizada) {
    const tr = document.createElement('tr');

    tr.innerHTML = `
      <td>${r.dataInicio}</td>
      <td>${r.dataFim}</td>
      <td class="text-capitalize">${r.semana}</td>
      <td>${r.horario}</td>
      <td>${r.carga}</td>
      <td>${r.modalidade}</td>
      <td>${r.treinamento}</td>
      <td>${r.local}</td>
      <td>${r.limite}</td>
      <td>${r.link ? `<a href="${r.link}" target="_blank" rel="noopener">Inscrever-se</a>` : '-'}</td>
    `;
    tbody.appendChild(tr);
  }
}

async function carregarTabelaTreinamentosResumo() {
  try {
    // *** IMPORTANTE ***
    // Substitua a linha abaixo pelo MESMO fetch usado em /planejamento-trimestral.html
    // (copie a chamada/rota/parâmetros já existentes lá).
    // Exemplo genérico com utilitário do projeto:
    const data = await chamarAPI('/planejamento/itens', 'GET');

    const lista = Array.isArray(data) ? data : (data.items || data.result || []);
    const normalizada = lista.map(normalizarParaResumo);
    renderTabelaResumo(normalizada);
  } catch (e) {
    console.error('Erro ao carregar treinamentos (resumo):', e);
  }
}

document.addEventListener('DOMContentLoaded', carregarTabelaTreinamentosResumo);

