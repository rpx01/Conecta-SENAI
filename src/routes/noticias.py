"""Rotas públicas para exibição das páginas de notícias."""

from flask import Blueprint, render_template

from src.auth import is_public

noticias_bp = Blueprint(
    "noticias",
    __name__,
    url_prefix="/noticias",
    template_folder="../static/noticias",
)


@noticias_bp.route("/", strict_slashes=False)
@is_public
def index():
    """Renderiza a página pública de notícias."""
    return render_template("index.html")


@noticias_bp.route("/index.html")
@is_public
def index_html():
    """Rota alternativa para a página pública de notícias."""
    return render_template("index.html")


@noticias_bp.route("/Index.html")
@is_public
def index_html_legacy():
    """Rota compatível com URLs legadas com letras maiúsculas."""
    return render_template("index.html")


@noticias_bp.route("/admin", strict_slashes=False)
def admin():
    """Renderiza a página protegida de gerenciamento de notícias."""
    return render_template("gerenciamento.html")
