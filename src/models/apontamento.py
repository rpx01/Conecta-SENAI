"""Modelo de apontamento de horas de instrutores."""
from datetime import datetime, date
from decimal import Decimal
from src.models import db

class Apontamento(db.Model):
    """Registro de horas trabalhadas para rateio de custos."""
    __tablename__ = 'apontamentos'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    horas = db.Column(db.Numeric(10, 2), nullable=False)
    descricao = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pendente')
    instrutor_id = db.Column(db.Integer, db.ForeignKey('instrutores.id'), nullable=False)
    centro_custo_id = db.Column(db.Integer, db.ForeignKey('centros_custo.id'), nullable=False)
    ocupacao_id = db.Column(db.Integer, db.ForeignKey('ocupacoes.id'))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    instrutor = db.relationship('Instrutor', backref='apontamentos', lazy=True)
    centro_custo = db.relationship('CentroCusto', backref='apontamentos', lazy=True)

    def __init__(self, data, horas, descricao, instrutor_id, centro_custo_id, status='Pendente', ocupacao_id=None):
        self.data = data if isinstance(data, date) else datetime.strptime(data, '%Y-%m-%d').date()
        self.horas = Decimal(horas)
        self.descricao = descricao
        self.status = status
        self.instrutor_id = instrutor_id
        self.centro_custo_id = centro_custo_id
        self.ocupacao_id = ocupacao_id

    def to_dict(self):
        return {
            'id': self.id,
            'data': self.data.isoformat() if self.data else None,
            'horas': float(self.horas) if self.horas is not None else None,
            'descricao': self.descricao,
            'status': self.status,
            'instrutor_id': self.instrutor_id,
            'centro_custo_id': self.centro_custo_id,
            'ocupacao_id': self.ocupacao_id,
        }

    def __repr__(self):
        return f'<Apontamento {self.id} - Instrutor {self.instrutor_id}>'
