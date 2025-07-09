"""Inicializacao do pacote de modelos."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .refresh_token import RefreshToken  # noqa: E402
from .recurso import Recurso  # noqa: E402

__all__ = [
    "db",
    "RefreshToken",
    "Recurso",
]
