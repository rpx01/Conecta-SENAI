(function () {
  const params = new URLSearchParams(window.location.search);
  const treinamentoId = params.get('treinamentoId');
  const nomeQS = params.get('nome');

  const form = document.getElementById('formInscricao');
  const submitButton = document.getElementById('btnEnviar');
  const nomeTreinamentoInput = document.getElementById('nomeTreinamento');

  if (nomeQS) {
    nomeTreinamentoInput.value = decodeURIComponent(nomeQS);
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const validator = window.FormValidation?.get(form);
    if (validator && !validator.validate()) {
      return;
    }

    const dataNascimentoIso = window.FormValidation
      ? window.FormValidation.sanitizeField(document.getElementById('dataNascimento'))
      : document.getElementById('dataNascimento').value;

    const payload = {
      matricula: document.getElementById('matricula').value?.trim(),
      treinamento_id: treinamentoId,
      nome_treinamento: nomeTreinamentoInput.value,
      tipo_treinamento: document.getElementById('tipoTreinamento').value?.trim(),
      nome_completo: document.getElementById('nomeCompleto').value?.trim(),
      naturalidade: document.getElementById('naturalidade').value?.trim(),
      email: document.getElementById('email').value?.trim(),
      data_nascimento: dataNascimentoIso,
      cpf: window.FormValidation
        ? window.FormValidation.sanitizeField(document.getElementById('cpf'))
        : document.getElementById('cpf').value?.trim(),
      empresa: document.getElementById('empresa').value?.trim(),
    };

    await executarAcaoComFeedback(submitButton, async () => {
      await chamarAPI('/api/inscricoes-treinamento', 'POST', payload);
      alert('Inscrição enviada com sucesso!');
      window.location.href = '/planejamento-treinamentos.html';
    });
  });
})();
