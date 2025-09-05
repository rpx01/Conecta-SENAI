// src/static/js/auth/forgot.js
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('forgotForm');
  if (!form) return;

  const emailEl = document.getElementById('email');
  const btn = document.getElementById('btnForgot');
  const msg = document.getElementById('forgotMsg');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = (emailEl.value || '').trim();

    btn.disabled = true;
    const originalText = btn.innerText;
    btn.innerText = 'Enviando...';
    msg.textContent = '';
    msg.className = '';

    try {
      const r = await fetch('/forgot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const data = await r.json().catch(() => ({}));
      const text = data.message || 'Se o e-mail existir, enviaremos as instruções.';
      msg.textContent = text;
      msg.className = r.ok ? 'alert alert-success' : 'alert alert-warning';
    } catch (err) {
      msg.textContent = 'Não foi possível enviar agora. Tente novamente em instantes.';
      msg.className = 'alert alert-danger';
    } finally {
      btn.disabled = false;
      btn.innerText = originalText;
    }
  });
});
