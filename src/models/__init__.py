"""Inicializacao do pacote de modelos."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

__all__ = [
    "db",
    "RefreshToken",
    "Recurso",
]

from .refresh_token import RefreshToken
from .recurso import Recurso
