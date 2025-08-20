// Conjunto de feriados municipais/estaduais/nacionais de Conceição do Mato Dentro (MG).
// Formato ISO: YYYY-MM-DD.
const FERIADOS_CMD = new Set([
  // Feriados Nacionais e Municipais de 2025
  "2025-01-01", // Confraternização Universal
  "2025-01-20", // Dia de São Sebastião (Feriado Municipal)
  "2025-03-03", // Carnaval (Ponto Facultativo)
  "2025-03-04", // Carnaval (Ponto Facultativo)
  "2025-03-05", // Quarta-feira de Cinzas (Ponto Facultativo)
  "2025-04-17", // Quinta-Feira Santa (Ponto Facultativo)
  "2025-04-18", // Sexta-Feira da Paixão
  "2025-04-21", // Tiradentes
  "2025-05-01", // Dia do Trabalhador
  "2025-06-19", // Corpus Christi
  "2025-06-24", // Aniversário da Cidade (Feriado Municipal)
  "2025-09-07", // Independência do Brasil
  "2025-10-12", // Nossa Senhora Aparecida
  "2025-11-02", // Finados
  "2025-11-15", // Proclamação da República
  "2025-12-25", // Natal
]);

function toISO(d) { return d.toISOString().slice(0, 10); }
function fromISO(iso) {
  const [y, m, day] = iso.split("-").map(Number);
  return new Date(y, m - 1, day);
}
function addDays(d, n) { const x = new Date(d); x.setDate(x.getDate() + n); return x; }
function isWeekend(d) { const wd = d.getDay(); return wd === 0 || wd === 6; }
function isHolidayCMD(d) { return FERIADOS_CMD.has(toISO(d)); }

/** Lista apenas os dias úteis (não sábado, não domingo e não feriado municipal) */
export function listarDiasUteis(inicioISO, fimISO) {
  let d = fromISO(inicioISO);
  const fim = fromISO(fimISO);
  const out = [];
  while (d <= fim) {
    if (!isWeekend(d) && !isHolidayCMD(d)) out.push(toISO(d));
    d = addDays(d, 1);
  }
  return out;
}

// Também expõe globalmente para páginas sem módulos ES.
window.DatasUtils = { listarDiasUteis };
