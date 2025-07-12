from src.models import db
from datetime import date

class Apontamento(db.Model):
    __tablename__ = 'apontamentos'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, default=date.today)
    horas = db.Column(db.Numeric(5, 2), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pendente') # Pendente, Aprovado, Rejeitado
    instrutor_id = db.Column(db.Integer, db.ForeignKey('instrutores.id'), nullable=False)
    centro_custo_id = db.Column(db.Integer, db.ForeignKey('centros_custo.id'), nullable=False)
    ocupacao_id = db.Column(db.Integer, db.ForeignKey('ocupacoes.id'), nullable=True)

    instrutor = db.relationship('Instrutor')
    centro_custo = db.relationship('CentroCusto')

    def to_dict(self):
        return {
            'id': self.id,
            'data': self.data.isoformat(),
            'horas': float(self.horas),
            'descricao': self.descricao,
            'status': self.status,
            'instrutor_id': self.instrutor_id,
            'instrutor_nome': self.instrutor.nome if self.instrutor else None,
            'centro_custo_id': self.centro_custo_id,
            'centro_custo_nome': self.centro_custo.nome if self.centro_custo else None
        }
