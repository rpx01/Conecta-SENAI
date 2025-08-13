"""Rotas de interface para planejamento."""
from datetime import date

from flask import render_template, g

from src.auth import require_roles, ROLE_ADMIN, ROLE_GESTOR, ROLE_USER

from . import bp


@bp.route("/")
@require_roles(ROLE_ADMIN, ROLE_GESTOR, ROLE_USER)
def index():
    return render_template(
        "planejamento/index.html", user_role=g.current_user.tipo.upper()
    )


@bp.route("/matriz")
@require_roles(ROLE_ADMIN, ROLE_GESTOR, ROLE_USER)
def matriz():
    current_year_month = date.today().strftime("%Y-%m")
    return render_template(
        "planejamento/matriz.html",
        user_role=g.current_user.tipo.upper(),
        current_year_month=current_year_month,
    )


@bp.route("/lista")
@require_roles(ROLE_ADMIN, ROLE_GESTOR, ROLE_USER)
def lista():
    current_year_month = date.today().strftime("%Y-%m")
    return render_template(
        "planejamento/lista.html",
        user_role=g.current_user.tipo.upper(),
        current_year_month=current_year_month,
    )
