import logging
import re
import time
from threading import Thread
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_mail import Message
from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash
from flask_wtf.csrf import generate_csrf, validate_csrf, CSRFError

from src.repositories.user_repository import UserRepository
from src.utils.tokens import generate_reset_token, confirm_reset_token
from src.extensions import mail

auth_reset_bp = Blueprint('auth_reset', __name__)

PASSWORD_RE = re.compile(r'^(?=.*[A-Za-z])(?=.*\d).{8,}$')


def _validate_password(password: str) -> bool:
    return bool(PASSWORD_RE.match(password))


@auth_reset_bp.get('/forgot')
def forgot_get():
    csrf_token = generate_csrf()
    return render_template('admin/forgot_password.html', csrf_token=csrf_token)


@auth_reset_bp.post('/forgot')
def forgot_post():
    time.sleep(1)
    try:
        validate_csrf(request.form.get('csrf_token'))
    except CSRFError:
        flash('Token CSRF inválido.', 'error')
        return redirect(url_for('auth_reset.forgot_get'))

    email = request.form.get('email', '').strip().lower()
    if email:
        try:
            validate_email(email)
            user = UserRepository.get_by_email(email)
        except EmailNotValidError:
            user = None
        if user:
            token = generate_reset_token(email)
            reset_url = f"{current_app.config['FRONTEND_BASE_URL']}/reset?token={token}"
            msg = Message(
                subject="Conecta SENAI - Redefinição de Senha",
                sender=current_app.config.get('MAIL_USERNAME'),
                recipients=[email]
            )
            msg.body = render_template('emails/reset_password.txt', reset_url=reset_url)
            msg.html = render_template('emails/reset_password.html', reset_url=reset_url)

            def send_async_email(app, message):
                with app.app_context():
                    try:
                        mail.send(message)
                    except Exception as e:  # pragma: no cover - envio de email
                        app.logger.error('Falha ao enviar e-mail de redefinição: %s', e)

            app_obj = current_app._get_current_object()
            Thread(target=send_async_email, args=(app_obj, msg), daemon=True).start()
    flash('Se o e-mail existir em nossa base, você receberá as instruções para redefinir sua senha.', 'info')
    return redirect('/admin/login.html')


@auth_reset_bp.get('/reset')
def reset_get():
    token = request.args.get('token', '')
    email = confirm_reset_token(token)
    if not email:
        flash('Link inválido ou expirado. Solicite uma nova redefinição.', 'error')
        return redirect(url_for('auth_reset.forgot_get'))
    csrf_token = generate_csrf()
    return render_template('admin/reset_password.html', token=token, csrf_token=csrf_token)


@auth_reset_bp.post('/reset')
def reset_post():
    try:
        validate_csrf(request.form.get('csrf_token'))
    except CSRFError:
        flash('Token CSRF inválido.', 'error')
        return redirect(url_for('auth_reset.forgot_get'))

    token = request.form.get('token', '')
    email = confirm_reset_token(token)
    if not email:
        flash('Link inválido ou expirado. Solicite uma nova redefinição.', 'error')
        return redirect(url_for('auth_reset.forgot_get'))

    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')
    if password != confirm or not _validate_password(password):
        flash('Senha inválida. Verifique os requisitos.', 'error')
        return redirect(url_for('auth_reset.reset_get', token=token))

    user = UserRepository.get_by_email(email)
    if not user:
        flash('Link inválido ou expirado. Solicite uma nova redefinição.', 'error')
        return redirect(url_for('auth_reset.forgot_get'))

    user.senha_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    UserRepository.commit()
    logging.info('Senha redefinida para usuário %s a partir do IP %s', user.id, request.remote_addr)
    flash('Senha redefinida com sucesso. Faça login novamente.', 'success')
    return redirect('/admin/login.html')
