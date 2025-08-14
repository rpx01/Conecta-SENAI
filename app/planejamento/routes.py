"""Rotas web para o módulo de planejamento."""
from flask import render_template

from app.planejamento import bp


@bp.route("/")
def index():
    """Página inicial do módulo de planejamento."""
    return render_template("planejamento/index.html")
