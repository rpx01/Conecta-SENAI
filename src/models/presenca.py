"""Modelo de presença em aula."""
from datetime import date
from src.models import db

class Presenca(db.Model):
    """Registros de presença para inscrições."""
    __tablename__ = 'presencas'

    id = db.Column(db.Integer, primary_key=True)
    inscricao_id = db.Column(db.Integer, db.ForeignKey('inscricoes.id'), nullable=False)
    data = db.Column(db.Date, default=date.today)
    presente = db.Column(db.Boolean, default=True)

    inscricao = db.relationship('Inscricao', backref=db.backref('presencas', lazy=True))

    def __init__(self, inscricao_id, data=None, presente=True):
        self.inscricao_id = inscricao_id
        self.data = data or date.today()
        self.presente = presente

    def to_dict(self):
        return {
            'id': self.id,
            'inscricao_id': self.inscricao_id,
            'data': self.data.isoformat(),
            'presente': self.presente,
        }

    def __repr__(self) -> str:
        return f'<Presenca {self.id}>'
