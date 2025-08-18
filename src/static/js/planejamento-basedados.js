// src/static/js/planejamento-basedados.js

(() => {
  // Estado único, sem 'mockData'
  const state = {
    publicosAlvo: [],
    locais: [],
    modalidades: [],
    horarios: [],
    cargasHorarias: [],
  };

  // Mapa de recursos: ajuste os endpoints se os seus forem diferentes
  const recursos = [
    {
      nome: 'Público Alvo',
      chave: 'publicosAlvo',
      endpoint: '/api/publicos-alvo',         // ajuste se necessário
      inputId: 'inputPublicoAlvo',
      btnSalvarId: 'btnSalvarPublicoAlvo',
      listaId: 'listaPublicosAlvo'
    },
    {
      nome: 'Local',
      chave: 'locais',
      endpoint: '/api/locais',                // ajuste se necessário
      inputId: 'inputLocal',
      btnSalvarId: 'btnSalvarLocal',
      listaId: 'listaLocais'
    },
    {
      nome: 'Modalidade',
      chave: 'modalidades',
      endpoint: '/api/modalidades',           // ajuste se necessário
      inputId: 'inputModalidade',
      btnSalvarId: 'btnSalvarModalidade',
      listaId: 'listaModalidades'
    },
    {
      nome: 'Horário',
      chave: 'horarios',
      endpoint: '/api/horarios',              // ajuste se necessário
      inputId: 'inputHorario',
      btnSalvarId: 'btnSalvarHorario',
      listaId: 'listaHorarios'
    },
    {
      nome: 'Carga Horária',
      chave: 'cargasHorarias',
      endpoint: '/api/cargas-horarias',       // ajuste se necessário
      inputId: 'inputCargaHoraria',
      btnSalvarId: 'btnSalvarCargaHoraria',
      listaId: 'listaCargasHorarias'
    }
  ];

  function qs(id) {
    return document.getElementById(id);
  }

  function renderLista(recurso) {
    const ul = qs(recurso.listaId);
    if (!ul) return;
    ul.innerHTML = '';
    state[recurso.chave].forEach((item) => {
      const li = document.createElement('li');
      li.className = 'list-group-item d-flex justify-content-between align-items-center';
      li.textContent = item.nome ?? item.descricao ?? String(item);
      ul.appendChild(li);
    });
  }

  async function carregar(recurso) {
    try {
      const dados = await chamarAPI(recurso.endpoint, 'GET'); // definido em app.js
      // Aceita array direto ou wrapper {items:[]}
      state[recurso.chave] = Array.isArray(dados) ? dados : (dados.items ?? []);
      renderLista(recurso);
    } catch (err) {
      console.error(`Falha ao carregar ${recurso.nome}:`, err);
      // Mostra a mesma mensagem que você está vendo hoje
      alert(`Não foi possível carregar dados de ${recurso.nome}.`);
    }
  }

  function registrarSalvar(recurso) {
    const btn = qs(recurso.btnSalvarId);
    const input = qs(recurso.inputId);
    if (!btn || !input) return;

    btn.addEventListener('click', (e) => {
      e.preventDefault();

      executarAcaoComFeedback(btn, async () => { // definido em app.js
        const nome = input.value.trim();
        if (!nome) {
          input.focus();
          return;
        }
        // Corpo mínimo esperado pela API
        const payload = { nome };

        const criado = await chamarAPI(recurso.endpoint, 'POST', payload);
        // Atualiza estado e UI
        state[recurso.chave].push(criado);
        renderLista(recurso);
        input.value = '';
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    // Carrega tudo em paralelo e registra os botões
    recursos.forEach((r) => {
      registrarSalvar(r);
    });
    Promise.all(recursos.map(carregar)).catch((e) => {
      // Erros já são tratados individualmente; este catch evita exceções não tratadas
      console.debug('Alguns recursos podem não ter carregado.', e);
    });
  });
})();

