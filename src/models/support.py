"""Modelos relacionados ao módulo de Suporte de TI."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Text, DateTime, Boolean

from src.models import db
from src.models.mixins import SerializerMixin


class SupportArea(db.Model, SerializerMixin):
    """Representa uma área responsável por um chamado de suporte."""

    __tablename__ = "support_areas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    tickets: Mapped[list[SupportTicket]] = relationship("SupportTicket", back_populates="area")


class SupportEquipmentType(db.Model, SerializerMixin):
    """Representa um tipo de equipamento atendido pelo suporte."""

    __tablename__ = "support_equipment_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    tickets: Mapped[list[SupportTicket]] = relationship("SupportTicket", back_populates="equipamento")


class SupportTicket(db.Model, SerializerMixin):
    """Chamado de suporte técnico."""

    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False)
    area_id: Mapped[int | None] = mapped_column(ForeignKey("support_areas.id"), nullable=True, index=True)
    equipamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("support_equipment_types.id"), nullable=True, index=True
    )
    patrimonio: Mapped[str | None] = mapped_column(String(100), nullable=True)
    numero_serie: Mapped[str | None] = mapped_column(String(100), nullable=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    urgencia: Mapped[str] = mapped_column(String(20), nullable=False, default="baixa", index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="aberto", index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    resolvido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    area: Mapped[SupportArea | None] = relationship("SupportArea", back_populates="tickets")
    equipamento: Mapped[SupportEquipmentType | None] = relationship(
        "SupportEquipmentType", back_populates="tickets"
    )
    anexos: Mapped[list[SupportTicketAttachment]] = relationship(
        "SupportTicketAttachment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SupportTicketAttachment(db.Model, SerializerMixin):
    """Arquivos anexados a um chamado de suporte."""

    __tablename__ = "support_ticket_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    caminho_relativo: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    ticket: Mapped[SupportTicket] = relationship("SupportTicket", back_populates="anexos")

    def url_publica(self) -> str:
        """Retorna a URL pública para acesso ao arquivo."""

        caminho = self.caminho_relativo.lstrip("/")
        return f"/static/{caminho}" if caminho else ""
