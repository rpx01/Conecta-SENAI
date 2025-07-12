from datetime import datetime
from src.models import db

class Apontamento(db.Model):
    """Registro de horas de instrutores."""
    __tablename__ = 'apontamentos'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    horas = db.Column(db.Numeric, nullable=False)
    descricao = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pendente')
    instrutor_id = db.Column(db.Integer, db.ForeignKey('instrutores.id'), nullable=False)
    centro_custo_id = db.Column(db.Integer, db.ForeignKey('centros_custo.id'), nullable=False)
    ocupacao_id = db.Column(db.Integer, db.ForeignKey('ocupacoes.id'))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    instrutor = db.relationship('Instrutor', backref='apontamentos', lazy=True)
    centro_custo = db.relationship('CentroCusto', backref='apontamentos', lazy=True)
    ocupacao = db.relationship('Ocupacao', backref='apontamentos', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'data': self.data.isoformat() if self.data else None,
            'horas': float(self.horas),
            'descricao': self.descricao,
            'status': self.status,
            'instrutor_id': self.instrutor_id,
            'centro_custo_id': self.centro_custo_id,
            'ocupacao_id': self.ocupacao_id
        }
