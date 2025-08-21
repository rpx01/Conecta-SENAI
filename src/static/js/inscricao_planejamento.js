document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const treinamento = params.get('treinamento') || '';
    const nomeInput = document.getElementById('nome-treinamento');
    if (nomeInput) {
        nomeInput.value = treinamento;
    }
});
