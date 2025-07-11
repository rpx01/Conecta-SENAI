"""Modelo de centro de custo."""
from src.models import db

class CentroCusto(db.Model):
    """Tabela de centros de custo para rateio."""
    __tablename__ = 'centros_custo'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    descricao = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)

    def __init__(self, nome, descricao=None, ativo=True):
        self.nome = nome
        self.descricao = descricao
        self.ativo = ativo

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'ativo': self.ativo,
        }

    def __repr__(self):
        return f'<CentroCusto {self.nome}>'
