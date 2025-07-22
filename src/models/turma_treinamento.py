"""Modelo de turma de treinamento."""
from datetime import datetime
from src.models import db


class TurmaTreinamento(db.Model):
    """Turma associada a um treinamento."""
    __tablename__ = 'turmas_treinamento'

    id = db.Column(db.Integer, primary_key=True)
    treinamento_id = db.Column(db.Integer, db.ForeignKey('treinamentos.id'), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_termino = db.Column(db.Date, nullable=False)
    data_treinamento_pratico = db.Column(db.Date)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inscricoes = db.relationship(
        'InscricaoTreinamento',
        backref='turma',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def __init__(self, treinamento_id, data_inicio, data_termino, data_treinamento_pratico=None):
        self.treinamento_id = treinamento_id
        self.data_inicio = data_inicio
        self.data_termino = data_termino
        self.data_treinamento_pratico = data_treinamento_pratico

    def to_dict(self):
        return {
            'id': self.id,
            'treinamento_id': self.treinamento_id,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_termino': self.data_termino.isoformat() if self.data_termino else None,
            'data_treinamento_pratico': self.data_treinamento_pratico.isoformat() if self.data_treinamento_pratico else None,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
        }

    def __repr__(self):
        return f"<TurmaTreinamento {self.id} do treinamento {self.treinamento_id}>"
