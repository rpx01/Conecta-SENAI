from src.models import db
from datetime import datetime

# Associacao entre Turma e Instrutor

turma_instrutores = db.Table('turma_instrutores',
    db.Column('turma_id', db.Integer, db.ForeignKey('treinamento_turmas.id'), primary_key=True),
    db.Column('instrutor_id', db.Integer, db.ForeignKey('instrutores.id'), primary_key=True)
)

class Treinamento(db.Model):
    __tablename__ = 'treinamentos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, unique=True)
    codigo = db.Column(db.String(50), unique=True, nullable=True)
    carga_horaria = db.Column(db.Integer, nullable=False)
    max_alunos = db.Column(db.Integer, nullable=False, default=20)
    materiais = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    materiais_didaticos = db.relationship(
        'MaterialDidatico',
        backref='treinamento',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    turmas = db.relationship(
        'TurmaTreinamento',
        backref='treinamento',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def to_dict(self):
        """Retorna representacao simples do treinamento."""
        return {
            'id': self.id,
            'nome': self.nome,
            'codigo': self.codigo,
            'carga_horaria': self.carga_horaria,
            'max_alunos': self.max_alunos,
            'materiais': self.materiais,
        }

    def to_dict_full(self):
        """Inclui materiais didáticos relacionados."""
        return {
            'id': self.id,
            'nome': self.nome,
            'codigo': self.codigo,
            'carga_horaria': self.carga_horaria,
            'max_alunos': self.max_alunos,
            'materiais': self.materiais,
            'materiais_didaticos': [m.to_dict() for m in self.materiais_didaticos],
        }

class TurmaTreinamento(db.Model):
    __tablename__ = 'treinamento_turmas'
    id = db.Column(db.Integer, primary_key=True)
    treinamento_id = db.Column(db.Integer, db.ForeignKey('treinamentos.id'), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='A realizar')

    instrutores = db.relationship('Instrutor', secondary=turma_instrutores, lazy='subquery',
                                  backref=db.backref('turmas_treinamento', lazy=True))
    inscricoes = db.relationship('Inscricao', backref='turma', lazy='dynamic', cascade='all, delete-orphan')

class MaterialDidatico(db.Model):
    __tablename__ = 'treinamento_materiais'
    id = db.Column(db.Integer, primary_key=True)
    treinamento_id = db.Column(db.Integer, db.ForeignKey('treinamentos.id'), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {'id': self.id, 'descricao': self.descricao, 'url': self.url}

class Inscricao(db.Model):
    __tablename__ = 'treinamento_inscricoes'
    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('treinamento_turmas.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)

# Alias para compatibilidade com versões anteriores
Turma = TurmaTreinamento
