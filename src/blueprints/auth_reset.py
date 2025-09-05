import logging
import re
from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    jsonify,
)
from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash
from flask_wtf.csrf import generate_csrf, validate_csrf, CSRFError

from src.repositories.user_repository import UserRepository
from src.utils.tokens import generate_reset_token, confirm_reset_token
from src.services.email_service import send_email_async

auth_reset_bp = Blueprint('auth_reset', __name__)

PASSWORD_RE = re.compile(r'^(?=.*[A-Za-z])(?=.*\d).{8,}$')


def _validate_password(password: str) -> bool:
    return bool(PASSWORD_RE.match(password))


@auth_reset_bp.get('/forgot')
def forgot_get():
    return render_template('admin/forgot_password.html')


@auth_reset_bp.post('/forgot')
def forgot_post():
    try:
        data = request.get_json(silent=True) or request.form
        email = (data.get('email') or '').strip().lower()
        if not email:
            return (
                jsonify({'ok': False, 'message': 'Informe um e-mail válido.'}),
                400,
            )

        try:
            validate_email(email)
            user = UserRepository.get_by_email(email)
        except EmailNotValidError:
            user = None
        except Exception:
            logging.exception('Erro ao buscar usuário para reset')
            user = None

        if user:
            try:
                token = generate_reset_token(email)
                reset_link = url_for(
                    'auth_reset.reset_get', token=token, _external=True
                )
                body_html = render_template(
                    'emails/reset_password.html',
                    reset_url=reset_link,
                    user=user,
                )
                subject = 'Conecta-SENAI | Recuperação de Senha'
                send_email_async(subject, user.email, body_html)
            except Exception:
                logging.exception('Falha ao enviar e-mail de reset')

        return (
            jsonify({
                'ok': True,
                'message': 'Se o e-mail existir, enviaremos as instruções.'
            }),
            200,
        )
    except Exception:
        logging.exception('Falha inesperada no /forgot')
        return (
            jsonify({
                'ok': True,
                'message': 'Se o e-mail existir, enviaremos as instruções.'
            }),
            200,
        )


@auth_reset_bp.get('/reset')
def reset_get():
    token = request.args.get('token', '')
    email = confirm_reset_token(token)
    if not email:
        flash(
            'Link inválido ou expirado. Solicite uma nova redefinição.',
            'error',
        )
        return redirect(url_for('auth_reset.forgot_get'))
    csrf_token = generate_csrf()
    return render_template(
        'admin/reset_password.html', token=token, csrf_token=csrf_token
    )


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
        flash(
            'Link inválido ou expirado. Solicite uma nova redefinição.',
            'error',
        )
        return redirect(url_for('auth_reset.forgot_get'))

    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')
    if password != confirm or not _validate_password(password):
        flash('Senha inválida. Verifique os requisitos.', 'error')
        return redirect(url_for('auth_reset.reset_get', token=token))

    user = UserRepository.get_by_email(email)
    if not user:
        flash(
            'Link inválido ou expirado. Solicite uma nova redefinição.',
            'error',
        )
        return redirect(url_for('auth_reset.forgot_get'))

    user.senha_hash = generate_password_hash(
        password, method='pbkdf2:sha256', salt_length=16
    )
    UserRepository.commit()
    logging.info(
        'Senha redefinida para usuário %s a partir do IP %s',
        user.id,
        request.remote_addr,
    )
    flash('Senha redefinida com sucesso. Faça login novamente.', 'success')
    return redirect('/admin/login.html')
