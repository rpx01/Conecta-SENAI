function pad2(n) { return String(n).padStart(2, '0'); }

// Constrói ISO local (evita fuso/hora) no formato YYYY-MM-DD
function toISODateLocal(d) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

function isWeekend(d) {
  const day = d.getDay(); // 0 = dom, 6 = sáb
  return day === 0 || day === 6;
}

function cloneDate(d) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function parseISODateToLocal(iso) {
  const [Y, M, D] = iso.split('-').map(Number);
  return new Date(Y, M - 1, D);
}

async function loadCMDHolidaysBetween(startDate, endDate) {
  const years = new Set();
  for (let y = startDate.getFullYear(); y <= endDate.getFullYear(); y++) {
    years.add(y);
  }
  const feriados = new Set();

  for (const y of years) {
    const url = `/static/data/feriados_cmd_${y}.json`;
    try {
      const resp = await fetch(url, { cache: 'no-store' });
      if (resp.ok) {
        const arr = await resp.json();
        arr.forEach(iso => feriados.add(iso));
      } else {
        console.warn('Não foi possível carregar feriados de', y, resp.status);
      }
    } catch (e) {
      console.warn('Falha ao carregar feriados de', y, e);
    }
  }
  return feriados;
}

function isBusinessDay(d, feriadosSet) {
  if (isWeekend(d)) return false;
  const iso = toISODateLocal(d);
  return !feriadosSet.has(iso);
}

function* eachBusinessDay(startDate, endDate, feriadosSet) {
  const d = cloneDate(startDate);
  while (d <= endDate) {
    if (isBusinessDay(d, feriadosSet)) {
      yield cloneDate(d);
    }
    d.setDate(d.getDate() + 1);
  }
}
