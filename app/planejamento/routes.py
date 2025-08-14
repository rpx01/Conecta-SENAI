"""Rotas web para o módulo de planejamento."""
from flask import render_template

from app.auth import require_roles, ROLE_ADMIN, ROLE_GESTOR, ROLE_USER
from app.planejamento import bp


@bp.route("/")
@require_roles(ROLE_ADMIN, ROLE_GESTOR, ROLE_USER)
def index():
    """Página inicial do módulo de planejamento."""
    return render_template("planejamento/index.html")


@bp.route("/matriz")
@require_roles(ROLE_ADMIN, ROLE_GESTOR, ROLE_USER)
def matriz():
    """Página com a matriz de planejamento."""
    return render_template("planejamento/matriz.html")


@bp.route("/lista")
@require_roles(ROLE_ADMIN, ROLE_GESTOR, ROLE_USER)
def lista():
    """Página com a lista de itens planejados."""
    return render_template("planejamento/lista.html")
