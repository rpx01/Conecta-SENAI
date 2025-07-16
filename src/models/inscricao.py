"""Modelo de inscrição em turma de treinamento."""
from datetime import datetime
from src.models import db

class Inscricao(db.Model):
    """Inscrições de usuários em turmas."""
    __tablename__ = 'inscricoes'

    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('treinamento_turmas.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    status = db.Column(db.String(20), default='inscrito')
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)

    turma = db.relationship('TurmaTreinamento', backref=db.backref('inscricoes', lazy=True))

    def __init__(self, turma_id, usuario_id, status='inscrito'):
        self.turma_id = turma_id
        self.usuario_id = usuario_id
        self.status = status

    def to_dict(self):
        return {
            'id': self.id,
            'turma_id': self.turma_id,
            'usuario_id': self.usuario_id,
            'status': self.status,
            'data_inscricao': self.data_inscricao.isoformat() if self.data_inscricao else None,
        }

    def __repr__(self) -> str:
        return f'<Inscricao {self.id}>'
