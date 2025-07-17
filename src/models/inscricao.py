"""Modelo de inscrição de usuários em turmas."""
from datetime import datetime
from src.models import db


class Inscricao(db.Model):
    """Representa a inscrição de um usuário em uma turma."""
    __tablename__ = 'inscricoes'

    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('turmas_treinamentos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    status = db.Column(db.String(20), default='inscrito')
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)

    presencas = db.relationship('Presenca', backref='inscricao', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'turma_id': self.turma_id,
            'usuario_id': self.usuario_id,
            'status': self.status,
            'data_inscricao': self.data_inscricao.isoformat() if self.data_inscricao else None,
        }

    def __repr__(self):
        return f'<Inscricao usuario={self.usuario_id} turma={self.turma_id}>'
