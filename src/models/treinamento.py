from src.models import db

# Tabela de associação para ligar instrutores qualificados a um treinamento
treinamento_instrutores = db.Table(
    'treinamento_instrutores',
    db.Column('treinamento_id', db.Integer, db.ForeignKey('treinamentos.id'), primary_key=True),
    db.Column('instrutor_id', db.Integer, db.ForeignKey('instrutores.id'), primary_key=True),
)

class Treinamento(db.Model):
    __tablename__ = 'treinamentos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, unique=True)
    codigo = db.Column(db.String(50), nullable=True, unique=True)
    carga_horaria = db.Column(db.Integer, nullable=False)

    instrutores_qualificados = db.relationship('Instrutor', secondary=treinamento_instrutores, lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'codigo': self.codigo,
            'carga_horaria': self.carga_horaria,
        }

    def __repr__(self) -> str:
        return f'<Treinamento {self.nome}>'
