"""Rotas web para o módulo de planejamento."""
from datetime import date
from flask import render_template, g, request

from app.auth import require_roles, ROLE_ADMIN, ROLE_GESTOR, ROLE_USER
from app.planejamento import bp


@bp.app_context_processor
def inject_globals():
    role = getattr(g, "current_role", request.headers.get("X-Role"))
    return {
        "user_role": role,
        "current_year_month": date.today().strftime("%Y-%m"),
    }


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
