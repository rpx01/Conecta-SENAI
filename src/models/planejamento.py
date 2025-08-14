from sqlalchemy import UniqueConstraint
from . import db


class Planejamento(db.Model):
    """Representa o planejamento de treinamentos."""

    __tablename__ = "planejamento"

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, index=True)
    turno = db.Column(
        db.Enum("MANHA", "TARDE", "NOITE", name="turno_enum"),
        nullable=False,
    )
    carga_horas = db.Column(db.Integer, nullable=True)
    modalidade = db.Column(
        db.Enum("Presencial", "Online", name="modalidade_enum"),
        nullable=True,
    )
    treinamento = db.Column(db.String(255), nullable=False)
    instrutor_id = db.Column(
        db.Integer,
        db.ForeignKey("instrutores.id"),
        nullable=False,
        index=True,
    )
    local = db.Column(db.String(255), nullable=True)
    cliente = db.Column(db.String(120), nullable=True)
    observacao = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum("Planejado", "Confirmado", "Cancelado", name="status_enum"),
        default="Planejado",
        nullable=False,
    )
    origem = db.Column(
        db.Enum("Manual", "Importado", name="origem_enum"),
        default="Manual",
        nullable=False,
    )
    criado_em = db.Column(db.DateTime, server_default=db.func.now())
    atualizado_em = db.Column(db.DateTime, onupdate=db.func.now())

    instrutor = db.relationship("Instrutor", backref=db.backref("planejamentos", lazy=True))

    __table_args__ = (
        UniqueConstraint(
            "data",
            "turno",
            "instrutor_id",
            name="uq_planejamento_slot_instrutor",
        ),
    )

    def to_dict(self):
        """Converte o objeto para um dicionário."""
        return {
            "id": self.id,
            "data": self.data.isoformat(),
            "turno": self.turno,
            "carga_horas": self.carga_horas,
            "modalidade": self.modalidade,
            "treinamento": self.treinamento,
            "instrutor_id": self.instrutor_id,
            "instrutor": self.instrutor.nome if self.instrutor else None,
            "local": self.local,
            "cliente": self.cliente,
            "observacao": self.observacao,
            "status": self.status,
        }
