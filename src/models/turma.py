from datetime import datetime
from src.models import db

class TurmaTreinamento(db.Model):
    __tablename__ = 'turmas_treinamento'
    id = db.Column(db.Integer, primary_key=True)
    treinamento_id = db.Column(db.Integer, db.ForeignKey('treinamentos.id'), nullable=False)
    data_inicio = db.Column(db.DateTime, nullable=False)
    data_fim = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='A realizar', nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    treinamento = db.relationship('Treinamento', backref='turmas')

    def to_dict(self):
        return {
            'id': self.id,
            'treinamento_id': self.treinamento_id,
            'treinamento': self.treinamento.to_dict() if self.treinamento else None,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_fim': self.data_fim.isoformat() if self.data_fim else None,
            'status': self.status,
        }

    def __repr__(self) -> str:
        return f'<TurmaTreinamento {self.id}>'
