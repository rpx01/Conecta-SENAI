"""Modelo de inscricao em treinamento."""
from datetime import datetime
from src.models import db


class InscricaoTreinamento(db.Model):
    """Inscricao de usuario em uma turma de treinamento."""
    __tablename__ = 'inscricoes_treinamento'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turmas_treinamento.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(20), nullable=False)
    data_nascimento = db.Column(db.Date)
    empresa = db.Column(db.String(100))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    usuario = db.relationship('User', backref='inscricoes_treinamento', lazy=True)

    def __init__(self, usuario_id, turma_id, nome, email, cpf, data_nascimento=None, empresa=None):
        self.usuario_id = usuario_id
        self.turma_id = turma_id
        self.nome = nome
        self.email = email
        self.cpf = cpf
        self.data_nascimento = data_nascimento
        self.empresa = empresa

    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'turma_id': self.turma_id,
            'nome': self.nome,
            'email': self.email,
            'cpf': self.cpf,
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None,
            'empresa': self.empresa,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
        }

    def __repr__(self):
        return f"<InscricaoTreinamento {self.id} usuario {self.usuario_id}>"
