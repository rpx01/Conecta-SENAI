from src.models import db

class CentroCusto(db.Model):
    __tablename__ = 'centros_custo'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255))
    ativo = db.Column(db.Boolean, default=True)

    def __init__(self, nome, descricao=None, ativo=True):
        self.nome = nome
        self.descricao = descricao
        self.ativo = ativo

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'ativo': self.ativo,
        }
