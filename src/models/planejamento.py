"""Model for storing planning items."""
from datetime import datetime
from sqlalchemy import Enum as SAEnum
from src.models import db


class PlanejamentoItem(db.Model):
    """Representa uma linha de planejamento trimestral."""
    __tablename__ = "planejamento_itens"

    id = db.Column(db.Integer, primary_key=True)
    row_id = db.Column(db.String(36), unique=True, nullable=False)
    lote_id = db.Column(db.String(36), nullable=False)
    data = db.Column(db.Date, nullable=False)
    semana = db.Column(db.String(20))
    horario = db.Column(db.String(50))
    carga_horaria = db.Column(db.String(50))
    modalidade = db.Column(db.String(50))
    treinamento = db.Column(db.String(100))
    cmd = db.Column(db.String(100))
    sjb = db.Column(db.String(100))
    sag_tombos = db.Column(db.String(100))
    instrutor = db.Column(db.String(100))
    local = db.Column(db.String(100))
    observacao = db.Column(db.String(255))
    sge_ativo = db.Column(db.Boolean, default=False)
    sge_link = db.Column(db.String(512))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        """Converte o item para dicionário."""
        return {
            "id": self.id,
            "rowId": self.row_id,
            "loteId": self.lote_id,
            "data": self.data.isoformat() if self.data else None,
            "semana": self.semana,
            "horario": self.horario,
            "cargaHoraria": self.carga_horaria,
            "modalidade": self.modalidade,
            "treinamento": self.treinamento,
            "cmd": self.cmd,
            "sjb": self.sjb,
            "sagTombos": self.sag_tombos,
            "instrutor": self.instrutor,
            "local": self.local,
            "observacao": self.observacao,
            "sge_ativo": self.sge_ativo,
            "sge_link": self.sge_link,
            "criadoEm": (
                self.criado_em.isoformat() if self.criado_em else None
            ),
            "atualizadoEm": (
                self.atualizado_em.isoformat() if self.atualizado_em else None
            ),
        }


class PlanejamentoBase(db.Model):
    """Base model for simple lookup tables in planejamento."""

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)

    def to_dict(self):
        return {"id": self.id, "nome": self.nome}


class Local(PlanejamentoBase):
    __tablename__ = "planejamento_locais"


class Modalidade(PlanejamentoBase):
    __tablename__ = "planejamento_modalidades"


class Horario(PlanejamentoBase):
    __tablename__ = "planejamento_horarios"

    TURNOS = (
        "manhã",
        "tarde",
        "noite",
        "manhã/tarde",
        "tarde/noite",
    )

    turno = db.Column(
        SAEnum(*TURNOS, name="turno_enum", native_enum=False),
        nullable=True,
    )

    def to_dict(self):
        dados = super().to_dict()
        dados["turno"] = self.turno
        return dados


class CargaHoraria(PlanejamentoBase):
    __tablename__ = "planejamento_cargas_horarias"


class PublicoAlvo(PlanejamentoBase):
    __tablename__ = "planejamento_publicos_alvo"


class PlanejamentoTreinamento(PlanejamentoBase):
    __tablename__ = "planejamento_treinamentos"
    carga_horaria = db.Column(db.Integer)

    def to_dict(self):
        dados = super().to_dict()
        dados["carga_horaria"] = self.carga_horaria
        return dados


class PlanejamentoBDItem(db.Model):
    """Simple item used by the planejamento base de dados page."""

    __tablename__ = "planejamento_bd_itens"

    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String, nullable=False)
    instrutor_id = db.Column(db.Integer, db.ForeignKey("instrutores.id"))

    instrutor = db.relationship("Instrutor", backref="planejamento_bd_itens")

    def to_dict(self):
        return {
            "id": self.id,
            "descricao": self.descricao,
            "instrutor_id": self.instrutor_id,
        }
