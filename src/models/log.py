from src.models import db
from datetime import datetime
from enum import Enum

class LogAcao(Enum):
    CRIACAO = "Criação"
    ATUALIZACAO = "Atualização"
    EXCLUSAO = "Exclusão"
    LOGIN = "Login"

class Log(db.Model):
    __tablename__ = 'logs_auditoria'

    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario_nome = db.Column(db.String(200), nullable=False)
    acao = db.Column(db.Enum(LogAcao), nullable=False)
    modelo_alvo = db.Column(db.String(100), nullable=False, index=True)
    id_alvo = db.Column(db.Integer)
    detalhes = db.Column(db.JSON)

    usuario = db.relationship('User', backref='logs')

    def to_dict(self):
        return {
            'id': self.id,
            'data_hora': self.data_hora.isoformat(),
            'usuario_nome': self.usuario_nome,
            'acao': self.acao.value,
            'modelo_alvo': self.modelo_alvo,
            'id_alvo': self.id_alvo,
            'detalhes': self.detalhes,
        }

