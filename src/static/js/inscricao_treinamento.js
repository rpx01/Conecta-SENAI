(function () {
  const params = new URLSearchParams(window.location.search);
  const treinamentoId = params.get('treinamentoId');
  const nomeQS = params.get('nome');

  const $nomeTreinamento = document.getElementById('nomeTreinamento');
  if (nomeQS) $nomeTreinamento.value = decodeURIComponent(nomeQS);

  const $cpf = document.getElementById('cpf');
  $cpf.addEventListener('input', (e) => {
    let v = e.target.value.replace(/\D/g, '').slice(0, 11);
    if (v.length > 3) v = v.slice(0,3) + '.' + v.slice(3);
    if (v.length > 7) v = v.slice(0,7) + '.' + v.slice(7);
    if (v.length > 11) v = v.slice(0,11) + '-' + v.slice(11);
    e.target.value = v;
  });

  document.getElementById('btnEnviar').addEventListener('click', async () => {
    const payload = {
      matricula: document.getElementById('matricula').value?.trim(),
      treinamento_id: treinamentoId,
      nome_treinamento: $nomeTreinamento.value,
      tipo_treinamento: document.getElementById('tipoTreinamento').value?.trim(),
      nome_completo: document.getElementById('nomeCompleto').value?.trim(),
      naturalidade: document.getElementById('naturalidade').value?.trim(),
      email: document.getElementById('email').value?.trim(),
      data_nascimento: document.getElementById('dataNascimento').value,
      cpf: document.getElementById('cpf').value?.trim(),
      empresa: document.getElementById('empresa').value?.trim(),
    };

    for (const [k, v] of Object.entries(payload)) {
      if (!v && k !== 'treinamento_id') { alert('Preencha todos os campos.'); return; }
    }

    await executarAcaoComFeedback(document.getElementById('btnEnviar'), async () => {
      await chamarAPI('/api/inscricoes-treinamento', 'POST', payload);
      alert('Inscrição enviada com sucesso!');
      window.location.href = '/planejamento-treinamentos.html';
    });
  });
})();
