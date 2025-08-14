"""Modelos para o módulo de planejamento."""
from flask_sqlalchemy import SQLAlchemy

# Inicializa um objeto SQLAlchemy para ser associado à aplicação.
db = SQLAlchemy()


class Planejamento(db.Model):
    """Representa um planejamento simples."""
    __tablename__ = "planejamentos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
