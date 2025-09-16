from flask import (
    Blueprint,
    current_app,
    flash,
    make_response,
    render_template,
    request,
)
from flask_wtf.csrf import generate_csrf

from conectasenai_api.models import db
from conectasenai_api.models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/register")
def register_page():
    """Renderiza a página de registro e define o cookie CSRF."""
    token = generate_csrf()
    secure_cookie = current_app.config.get("COOKIE_SECURE", False)
    samesite = current_app.config.get("COOKIE_SAMESITE", "Lax")
    resp = make_response(render_template("admin/register.html", csrf_token=token))
    resp.set_cookie("csrf_token", token, secure=secure_cookie, samesite=samesite)
    return resp


@auth_bp.route("/login", methods=["GET", "POST"])
def login_page():
    """Renderiza a página de login e exibe mensagem em caso de falha."""
    token = generate_csrf()
    secure_cookie = current_app.config.get("COOKIE_SECURE", False)
    samesite = current_app.config.get("COOKIE_SAMESITE", "Lax")

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")

        usuario = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if not usuario or not usuario.check_senha(senha):
            flash("Usuário ou senha inválidos", "error")

    resp = make_response(render_template("admin/login.html", csrf_token=token))
    resp.set_cookie("csrf_token", token, secure=secure_cookie, samesite=samesite)
    return resp
