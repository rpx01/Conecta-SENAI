// JavaScript for Planejamento Trimestral page

/* global bootstrap, showToast, escapeHTML */
document.addEventListener('DOMContentLoaded', () => {
  const modalEl = document.getElementById('modal-planejamento');
  const modal = new bootstrap.Modal(modalEl);
  const btnAdd = document.getElementById('btn-adicionar-planejamento');
  const form = document.getElementById('form-planejamento');
  const preview = document.getElementById('linhaPreview');
  const tbody = document.querySelector('#tabela-planejamento-trimestral tbody');

  const registros = [];
  let baseCarregada = false;
  let base = {};

  const diasSemana = ['domingo', 'segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado'];

  btnAdd.addEventListener('click', async () => {
    if (!baseCarregada) {
      try {
        await carregarBase();
        popularSelects();
        baseCarregada = true;
      } catch (e) {
        console.error(e);
        showToast('Não foi possível carregar a base de dados.', 'danger');
        return;
      }
    }
    form.reset();
    preview.textContent = '';
    modal.show();
  });

  form.inicio.addEventListener('change', atualizarPreview);
  form.fim.addEventListener('change', atualizarPreview);

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const inicio = form.inicio.value;
    const fim = form.fim.value;
    if (!inicio || !fim) {
      showToast('Data de início e término são obrigatórias.', 'warning');
      return;
    }
    if (fim < inicio) {
      showToast('A data de término deve ser igual ou posterior à de início.', 'warning');
      return;
    }

    const horario = form.horario.value;
    const carga = form.carga_horaria.value;
    const modalidade = form.modalidade.value;
    const treinamento = form.treinamento.value;
    const instrutor = form.instrutor.value;
    const local = form.local.value;
    if (!horario || !carga || !modalidade || !treinamento || !instrutor || !local) {
      showToast('Preencha todos os campos obrigatórios.', 'warning');
      return;
    }

    const cmd = getMulti(form.cmd);
    const sjb = getMulti(form.sjb);
    const sag = getMulti(form.sag_tombos);
    const observacao = form.observacao.value;

    const inicioDate = new Date(inicio);
    const fimDate = new Date(fim);
    for (let d = new Date(inicioDate); d <= fimDate; d.setDate(d.getDate() + 1)) {
      const dataStr = d.toISOString().split('T')[0];
      registros.push({
        inicio: dataStr,
        fim: dataStr,
        semana: diasSemana[d.getDay()],
        horario,
        carga,
        modalidade,
        treinamento,
        cmd,
        sjb,
        sag,
        instrutor,
        local,
        observacao,
      });
    }
    registros.sort((a, b) => new Date(a.inicio) - new Date(b.inicio));
    renderTabela();
    modal.hide();
    form.reset();
  });

  tbody.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-index]');
    if (btn) {
      const { index } = btn.dataset;
      registros.splice(Number(index), 1);
      renderTabela();
    }
  });

  function atualizarPreview() {
    const { inicio, fim } = form;
    preview.textContent = '';
    if (inicio.value && fim.value && fim.value >= inicio.value) {
      const count = Math.floor((new Date(fim.value) - new Date(inicio.value)) / 86400000) + 1;
      preview.textContent = `Serão criadas ${count} linha${count > 1 ? 's' : ''}.`;
    }
  }

  function getMulti(select) {
    return Array.from(select.selectedOptions).map((o) => o.value).join(', ');
  }

  function formatarData(iso) {
    return new Date(iso).toLocaleDateString('pt-BR');
  }

  function renderTabela() {
    tbody.innerHTML = '';
    registros.forEach((r, index) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${escapeHTML(formatarData(r.inicio))}</td>
        <td>${escapeHTML(formatarData(r.fim))}</td>
        <td>${escapeHTML(r.semana)}</td>
        <td>${escapeHTML(r.horario)}</td>
        <td>${escapeHTML(r.carga)}</td>
        <td>${escapeHTML(r.modalidade)}</td>
        <td>${escapeHTML(r.treinamento)}</td>
        <td>${escapeHTML(r.cmd)}</td>
        <td>${escapeHTML(r.sjb)}</td>
        <td>${escapeHTML(r.sag)}</td>
        <td>${escapeHTML(r.instrutor)}</td>
        <td>${escapeHTML(r.local)}</td>
        <td>${escapeHTML(r.observacao)}</td>
        <td class="text-end"><button type="button" class="btn btn-sm btn-outline-danger" data-index="${index}"><i class="bi bi-trash"></i></button></td>
      `;
      tbody.appendChild(tr);
    });
  }

  async function carregarBase() {
    const resp = await fetch('/planejamento-basedados.html');
    const html = await resp.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const extrair = (id) => {
      const set = new Set();
      doc.querySelectorAll(`#${id} tbody tr td:first-child`).forEach((td) => {
        const txt = td.textContent.trim();
        if (txt) set.add(txt);
      });
      return Array.from(set).sort((a, b) => a.localeCompare(b, 'pt-BR'));
    };
    base = {
      horario: extrair('tabela-horario'),
      carga_horaria: extrair('tabela-cargahoraria'),
      modalidade: extrair('tabela-modalidade'),
      treinamento: extrair('tabela-treinamento'),
      publico: extrair('tabela-publico-alvo'),
      instrutor: extrair('tabela-instrutor'),
      local: extrair('tabela-local'),
    };
  }

  function popularSelects() {
    preencher('horario', base.horario);
    preencher('carga_horaria', base.carga_horaria);
    preencher('modalidade', base.modalidade);
    preencher('treinamento', base.treinamento);
    preencher('cmd', base.publico, true);
    preencher('sjb', base.publico, true);
    preencher('sag_tombos', base.publico, true);
    preencher('instrutor', base.instrutor);
    preencher('local', base.local);
  }

  function preencher(id, valores, multiple = false) {
    const select = document.getElementById(id);
    if (!select) return;
    select.innerHTML = multiple ? '' : '<option value="">Selecione...</option>';
    valores.forEach((v) => {
      const opt = document.createElement('option');
      opt.value = v;
      opt.textContent = v;
      select.appendChild(opt);
    });
  }
});
