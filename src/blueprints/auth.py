from flask import Blueprint, render_template, make_response, current_app
from flask_wtf.csrf import generate_csrf

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/register")
def register_page():
    """Renderiza a página de registro e define o cookie CSRF."""
    token = generate_csrf()
    secure_cookie = current_app.config.get("COOKIE_SECURE", True)
    resp = make_response(render_template("admin/register.html", csrf_token=token))
    resp.set_cookie("csrf_token", token, secure=secure_cookie, samesite="Strict")
    return resp
