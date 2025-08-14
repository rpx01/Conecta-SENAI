"""Blueprint do módulo de planejamento."""
from flask import Blueprint

bp = Blueprint("planejamento", __name__)

from app.planejamento import routes, api  # noqa: F401,E402
