from datetime import datetime, date
from src.models import db

class Apontamento(db.Model):
    __tablename__ = 'apontamentos'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    horas = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pendente')
    instrutor_id = db.Column(db.Integer, db.ForeignKey('instrutores.id'), nullable=False)
    centro_custo_id = db.Column(db.Integer, db.ForeignKey('centros_custo.id'))
    ocupacao_id = db.Column(db.Integer, db.ForeignKey('ocupacoes.id'))

    instrutor = db.relationship('Instrutor', backref='apontamentos')
    centro_custo = db.relationship('CentroCusto', backref='apontamentos')

    def __init__(self, data, horas, descricao=None, status='pendente', instrutor_id=None,
                 centro_custo_id=None, ocupacao_id=None):
        self.data = data if isinstance(data, date) else datetime.strptime(data, '%Y-%m-%d').date()
        self.horas = horas
        self.descricao = descricao
        self.status = status
        self.instrutor_id = instrutor_id
        self.centro_custo_id = centro_custo_id
        self.ocupacao_id = ocupacao_id

    def to_dict(self):
        return {
            'id': self.id,
            'data': self.data.isoformat() if self.data else None,
            'horas': self.horas,
            'descricao': self.descricao,
            'status': self.status,
            'instrutor_id': self.instrutor_id,
            'centro_custo_id': self.centro_custo_id,
            'ocupacao_id': self.ocupacao_id,
        }
