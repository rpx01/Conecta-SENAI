from flask import Blueprint, render_template

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/register")
def register_page():
    """Renderiza a página de registro."""
    return render_template("admin/register.html")
