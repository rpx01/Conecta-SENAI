"""Modelos relacionados a treinamentos."""

"""Modelos relacionados a treinamentos."""

from datetime import datetime

from src.models import db


class Treinamento(db.Model):
    """Modelo de treinamento oferecido."""

    __tablename__ = "treinamentos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    # Colunas adicionais
    capacidade_maxima = db.Column(db.Integer)
    carga_horaria = db.Column(db.Integer)
    tem_pratica = db.Column(db.Boolean, default=False)
    links_materiais = db.Column(db.JSON)
    conteudo_programatico = db.Column(db.Text, nullable=True)

    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    turmas = db.relationship(
        "TurmaTreinamento", back_populates="treinamento", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "codigo": self.codigo,
            "capacidade_maxima": self.capacidade_maxima,
            "carga_horaria": self.carga_horaria,
            "tem_pratica": self.tem_pratica,
            "links_materiais": self.links_materiais or [],
            "conteudo_programatico": self.conteudo_programatico,
        }

    def __repr__(self):
        return f"<Treinamento {self.codigo}>"


class TurmaTreinamento(db.Model):
    """Turmas associadas a um treinamento."""

    __tablename__ = "turmas_treinamento"

    id = db.Column(db.Integer, primary_key=True)
    treinamento_id = db.Column(
        db.Integer, db.ForeignKey("treinamentos.id"), nullable=False
    )
    data_inicio = db.Column(db.Date, nullable=False)
    data_termino = db.Column("data_fim", db.Date, nullable=False)
    data_treinamento_pratico = db.Column(db.Date)
    status = db.Column(db.String(20), nullable=False, default="aberta")

    treinamento = db.relationship(
        "Treinamento", back_populates="turmas"
    )
    inscricoes = db.relationship(
        "InscricaoTreinamento", backref="turma", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "treinamento_id": self.treinamento_id,
            "nome_treinamento": self.treinamento.nome if self.treinamento else "N/A",
            "data_inicio": self.data_inicio.strftime("%Y-%m-%d"),
            "data_termino": self.data_termino.strftime("%Y-%m-%d"),
            "data_treinamento_pratico": self.data_treinamento_pratico.strftime("%Y-%m-%d") if self.data_treinamento_pratico else None,
            "status": self.status,
            "inscritos": self.inscricoes.count(),
        }

    def __repr__(self):
        return f"<TurmaTreinamento {self.id} - Treinamento {self.treinamento_id}>"


class InscricaoTreinamento(db.Model):
    """Inscricoes de usuarios em turmas de treinamento."""

    __tablename__ = "inscricoes_treinamento"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    turma_id = db.Column(
        db.Integer, db.ForeignKey("turmas_treinamento.id"), nullable=False
    )
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(20), nullable=False)
    data_nascimento = db.Column(db.Date)
    empresa = db.Column(db.String(150))
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "turma_id": self.turma_id,
            "nome": self.nome,
            "email": self.email,
            "cpf": self.cpf,
            "data_nascimento": self.data_nascimento.strftime("%Y-%m-%d") if self.data_nascimento else None,
            "empresa": self.empresa,
            "data_inscricao": self.data_inscricao.isoformat(),
        }

    def __repr__(self):
        return f"<InscricaoTreinamento {self.id} - Turma {self.turma_id}>"
