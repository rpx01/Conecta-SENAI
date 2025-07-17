"""Modelo de registro de presença nas aulas."""
from datetime import date
from src.models import db


class Presenca(db.Model):
    """Registra a presença de um inscrito em determinada data."""
    __tablename__ = 'presencas'

    id = db.Column(db.Integer, primary_key=True)
    inscricao_id = db.Column(db.Integer, db.ForeignKey('inscricoes.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    presente = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'inscricao_id': self.inscricao_id,
            'data': self.data.isoformat() if self.data else None,
            'presente': self.presente,
        }

    def __repr__(self):
        return f'<Presenca inscricao={self.inscricao_id} data={self.data}>'
