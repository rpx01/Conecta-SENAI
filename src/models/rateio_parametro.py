"""Modelo de parâmetros de rateio."""
from datetime import datetime
from src.models import db

class RateioParametro(db.Model):
    """Parâmetros para cálculo de rateio de instrutores."""
    __tablename__ = 'rateio_parametros'

    id = db.Column(db.Integer, primary_key=True)
    filial = db.Column(db.String(100), nullable=False)
    uo = db.Column(db.String(100), nullable=False)
    cr = db.Column(db.String(50), nullable=False)
    classe_valor = db.Column(db.String(100), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'filial': self.filial,
            'uo': self.uo,
            'cr': self.cr,
            'classe_valor': self.classe_valor,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
        }
