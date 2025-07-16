"""Modelo de treinamento."""
from datetime import datetime
from src.models import db

class Treinamento(db.Model):
    """Catálogo de treinamentos."""
    __tablename__ = 'treinamentos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    carga_horaria = db.Column(db.Integer)
    status = db.Column(db.String(20), default='ativo')
    descricao = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, nome, codigo, carga_horaria=None, status='ativo', descricao=None):
        self.nome = nome
        self.codigo = codigo
        self.carga_horaria = carga_horaria
        self.status = status
        self.descricao = descricao

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'codigo': self.codigo,
            'carga_horaria': self.carga_horaria,
            'status': self.status,
            'descricao': self.descricao,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
        }

    def __repr__(self) -> str:
        return f'<Treinamento {self.codigo}>'
