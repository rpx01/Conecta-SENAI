from flask import Blueprint

bp = Blueprint('planejamento', __name__)

from . import routes, api, models  # noqa: F401
