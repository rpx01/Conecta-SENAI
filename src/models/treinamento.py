"""Modelo de treinamento."""
from datetime import datetime
from src.models import db


class Treinamento(db.Model):
    """Representa um treinamento oferecido."""
    __tablename__ = 'treinamentos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(50), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    carga_horaria = db.Column(db.Integer)
    status = db.Column(db.String(20), default='ativo')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    turmas = db.relationship('TurmaTreinamento', backref='treinamento', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'codigo': self.codigo,
            'descricao': self.descricao,
            'carga_horaria': self.carga_horaria,
            'status': self.status,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
        }

    def __repr__(self):
        return f'<Treinamento {self.codigo}>'
