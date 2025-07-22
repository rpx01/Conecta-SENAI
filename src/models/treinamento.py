"""Modelos relacionados a treinamentos."""
from datetime import datetime
from src.models import db


class Treinamento(db.Model):
    """Modelo de treinamento."""
    __tablename__ = 'treinamentos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(50), nullable=False, unique=True)
    capacidade_maxima = db.Column(db.Integer)
    carga_horaria = db.Column(db.Integer)
    possui_treinamento_pratico = db.Column(db.Boolean, default=False)
    links_materiais = db.Column(db.JSON, default=list)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    turmas = db.relationship(
        'TurmaTreinamento',
        backref='treinamento',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def __init__(self, nome, codigo, capacidade_maxima=None, carga_horaria=None,
                 possui_treinamento_pratico=False, links_materiais=None):
        self.nome = nome
        self.codigo = codigo
        self.capacidade_maxima = capacidade_maxima
        self.carga_horaria = carga_horaria
        self.possui_treinamento_pratico = possui_treinamento_pratico
        self.links_materiais = links_materiais or []

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'codigo': self.codigo,
            'capacidade_maxima': self.capacidade_maxima,
            'carga_horaria': self.carga_horaria,
            'possui_treinamento_pratico': self.possui_treinamento_pratico,
            'links_materiais': self.links_materiais,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
        }

    def __repr__(self):
        return f"<Treinamento {self.codigo}>"
