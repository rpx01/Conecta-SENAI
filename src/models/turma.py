"""Modelo de turma de treinamento."""
from datetime import datetime
from src.models import db

class TurmaTreinamento(db.Model):
    """Turmas vinculadas a um treinamento."""
    __tablename__ = 'treinamento_turmas'

    id = db.Column(db.Integer, primary_key=True)
    treinamento_id = db.Column(db.Integer, db.ForeignKey('treinamentos.id'), nullable=False)
    nome = db.Column(db.String(100))
    data_inicio = db.Column(db.Date)
    data_fim = db.Column(db.Date)
    status = db.Column(db.String(20), default='aberta')
    vagas = db.Column(db.Integer)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    treinamento = db.relationship('Treinamento', backref=db.backref('turmas', lazy=True))

    def __init__(self, treinamento_id, nome=None, data_inicio=None, data_fim=None, status='aberta', vagas=None):
        self.treinamento_id = treinamento_id
        self.nome = nome
        self.data_inicio = data_inicio
        self.data_fim = data_fim
        self.status = status
        self.vagas = vagas

    def to_dict(self):
        return {
            'id': self.id,
            'treinamento_id': self.treinamento_id,
            'nome': self.nome,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_fim': self.data_fim.isoformat() if self.data_fim else None,
            'status': self.status,
            'vagas': self.vagas,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
        }

    def __repr__(self) -> str:
        return f'<Turma {self.id}>'
