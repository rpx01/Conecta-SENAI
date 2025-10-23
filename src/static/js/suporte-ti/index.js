document.addEventListener('DOMContentLoaded', async () => {
    if (!(await verificarAutenticacao())) return;

    const usuario = getUsuarioLogado();
    if (usuario) {
        const spanUsuario = document.getElementById('usuarioAtual');
        if (spanUsuario) {
            spanUsuario.textContent = `Olá, ${usuario.nome}`;
        }
    }
});
