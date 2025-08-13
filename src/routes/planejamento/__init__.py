"""Blueprint do módulo de planejamento."""
from flask import Blueprint

bp = Blueprint("planejamento", __name__)

from . import routes, api  # noqa: E402,F401
