from src.models import db
from datetime import datetime

# Tabela de associação entre Turma e Instrutor (Muitos para Muitos)
turma_instrutores = db.Table(
    'turma_instrutores',
    db.Column('turma_id', db.Integer, db.ForeignKey('treinamento_turmas.id'), primary_key=True),
    db.Column('instrutor_id', db.Integer, db.ForeignKey('instrutores.id'), primary_key=True)
)


class Treinamento(db.Model):
    """Modelo para o catálogo de treinamentos."""

    __tablename__ = 'treinamentos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, unique=True)
    codigo = db.Column(db.String(50), unique=True, nullable=True)
    carga_horaria = db.Column(db.Integer, nullable=False)

    materiais = db.relationship('MaterialDidatico', backref='treinamento', lazy=True, cascade='all, delete-orphan')
    turmas = db.relationship('TurmaTreinamento', backref='treinamento', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'codigo': self.codigo,
            'carga_horaria': self.carga_horaria,
            'materiais': [m.to_dict() for m in self.materiais],
        }

    def to_dict_full(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'codigo': self.codigo,
            'carga_horaria': self.carga_horaria,
            'materiais': [m.to_dict() for m in self.materiais],
        }


class TurmaTreinamento(db.Model):
    """Modelo para as turmas de um treinamento."""

    __tablename__ = 'treinamento_turmas'
    id = db.Column(db.Integer, primary_key=True)
    treinamento_id = db.Column(db.Integer, db.ForeignKey('treinamentos.id'), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='A realizar')  # 'A realizar', 'Em andamento', 'Concluída', 'Cancelada'

    instrutores = db.relationship(
        'Instrutor',
        secondary=turma_instrutores,
        lazy='subquery',
        backref=db.backref('turmas_treinamento', lazy=True),
    )

    inscricoes = db.relationship('Inscricao', backref='turma', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'treinamento_id': self.treinamento_id,
            'treinamento_nome': self.treinamento.nome if self.treinamento else None,
            'data_inicio': self.data_inicio.isoformat(),
            'data_fim': self.data_fim.isoformat(),
            'status': self.status,
            'instrutores': [i.to_dict() for i in self.instrutores],
            'participantes': [i.usuario.to_dict() for i in self.inscricoes],
        }


class MaterialDidatico(db.Model):
    """Modelo para materiais didáticos."""

    __tablename__ = 'treinamento_materiais'
    id = db.Column(db.Integer, primary_key=True)
    treinamento_id = db.Column(db.Integer, db.ForeignKey('treinamentos.id'), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {'id': self.id, 'descricao': self.descricao, 'url': self.url}


class Inscricao(db.Model):
    """Modelo para inscrição de um usuário em uma turma."""

    __tablename__ = 'treinamento_inscricoes'
    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('treinamento_turmas.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('User', backref='inscricoes_treinamento')
    presencas = db.relationship('ListaPresenca', backref='inscricao', lazy=True, cascade='all, delete-orphan')


class ListaPresenca(db.Model):
    """Modelo para a lista de presença."""

    __tablename__ = 'treinamento_presenca'
    id = db.Column(db.Integer, primary_key=True)
    inscricao_id = db.Column(db.Integer, db.ForeignKey('treinamento_inscricoes.id'), nullable=False)
    data_aula = db.Column(db.Date, nullable=False)
    presente = db.Column(db.Boolean, default=False)
