"""Modelo de lançamentos de rateio."""
from datetime import datetime, date
from src.models import db

class RateioLancamento(db.Model):
    """Lançamentos mensais por instrutor."""
    __tablename__ = 'rateio_lancamentos'
    __table_args__ = (db.UniqueConstraint('instrutor_id', 'mes', 'ano', name='uix_instrutor_mes_ano'),)

    id = db.Column(db.Integer, primary_key=True)
    instrutor_id = db.Column(db.Integer, db.ForeignKey('instrutores.id'), nullable=False)
    parametro_id = db.Column(db.Integer, db.ForeignKey('rateio_parametros.id'), nullable=False)
    data_referencia = db.Column(db.Date, nullable=False)
    mes = db.Column(db.Integer, nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    horas_trabalhadas = db.Column(db.Float, nullable=False)
    observacoes = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parametro = db.relationship('RateioParametro', backref='lancamentos')

    def __init__(self, instrutor_id, parametro_id, data_referencia, valor_total, horas_trabalhadas, observacoes=None):
        self.instrutor_id = instrutor_id
        self.parametro_id = parametro_id
        if isinstance(data_referencia, str):
            data_referencia = datetime.strptime(data_referencia, '%Y-%m-%d').date()
        self.data_referencia = data_referencia
        self.mes = data_referencia.month
        self.ano = data_referencia.year
        self.valor_total = valor_total
        self.horas_trabalhadas = horas_trabalhadas
        self.observacoes = observacoes

    def to_dict(self):
        return {
            'id': self.id,
            'instrutor_id': self.instrutor_id,
            'parametro_id': self.parametro_id,
            'data_referencia': self.data_referencia.isoformat(),
            'mes': self.mes,
            'ano': self.ano,
            'valor_total': self.valor_total,
            'horas_trabalhadas': self.horas_trabalhadas,
            'observacoes': self.observacoes,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
        }
