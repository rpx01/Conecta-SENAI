"""Modelos de chamados do módulo de suporte de TI."""
from datetime import datetime

from src.models import db


class SuporteChamado(db.Model):
    """Representa um chamado aberto pelos usuários para suporte de TI."""

    __tablename__ = "suporte_chamados"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    area = db.Column(db.String(120), nullable=False)
    tipo_equipamento_id = db.Column(
        db.Integer,
        db.ForeignKey("suporte_tipos_equipamento.id"),
        nullable=False,
    )
    patrimonio = db.Column(db.String(120), nullable=True)
    numero_serie = db.Column(db.String(120), nullable=True)
    descricao_problema = db.Column(db.Text, nullable=False)
    nivel_urgencia = db.Column(db.String(20), nullable=False, default="Baixo")
    status = db.Column(db.String(20), nullable=False, default="Aberto")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = db.relationship("User", backref="suporte_chamados")
    tipo_equipamento = db.relationship("SuporteTipoEquipamento", backref="chamados")
    anexos = db.relationship(
        "SuporteAnexo",
        back_populates="chamado",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - representação simples
        return f"<SuporteChamado id={self.id} status={self.status!r}>"
