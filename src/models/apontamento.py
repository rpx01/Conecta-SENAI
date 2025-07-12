"""Modelo de Apontamento de horas."""
from src.models import db
from datetime import datetime

class Apontamento(db.Model):
    __tablename__ = 'apontamentos'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    horas = db.Column(db.Numeric(10, 2), nullable=False)
    descricao = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pendente')
    instrutor_id = db.Column(db.Integer, db.ForeignKey('instrutores.id'), nullable=False)
    centro_custo_id = db.Column(db.Integer, db.ForeignKey('centros_custo.id'), nullable=False)
    ocupacao_id = db.Column(db.Integer, db.ForeignKey('ocupacoes.id'), nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    instrutor = db.relationship('Instrutor', backref='apontamentos')
    centro_custo = db.relationship('CentroCusto', backref='apontamentos')

    def valor_total(self):
        custo = getattr(self.instrutor, 'custo_hora', 0) or 0
        return float(self.horas) * float(custo)

    def to_dict(self):
        return {
            'id': self.id,
            'data': self.data.isoformat() if self.data else None,
            'horas': float(self.horas),
            'descricao': self.descricao,
            'status': self.status,
            'instrutor_id': self.instrutor_id,
            'centro_custo_id': self.centro_custo_id,
            'ocupacao_id': self.ocupacao_id,
            'valor_total': self.valor_total()
        }

    def __repr__(self):
        return f'<Apontamento {self.id}>'
