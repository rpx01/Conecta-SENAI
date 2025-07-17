"""Modelo de turma vinculada a um treinamento."""
from datetime import datetime, date
from src.models import db


class TurmaTreinamento(db.Model):
    """Turma de um treinamento."""
    __tablename__ = 'turmas_treinamentos'

    id = db.Column(db.Integer, primary_key=True)
    treinamento_id = db.Column(db.Integer, db.ForeignKey('treinamentos.id'), nullable=False)
    nome = db.Column(db.String(100))
    data_inicio = db.Column(db.Date)
    data_fim = db.Column(db.Date)
    vagas = db.Column(db.Integer)
    status = db.Column(db.String(20), default='aberta')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inscricoes = db.relationship('Inscricao', backref='turma', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'treinamento_id': self.treinamento_id,
            'nome': self.nome,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_fim': self.data_fim.isoformat() if self.data_fim else None,
            'vagas': self.vagas,
            'status': self.status,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
        }

    def __repr__(self):
        return f'<TurmaTreinamento {self.id} do treinamento {self.treinamento_id}>'
