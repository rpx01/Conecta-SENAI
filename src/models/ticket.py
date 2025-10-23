"""Modelos SQLAlchemy para o módulo de chamados de TI."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Index, UniqueConstraint

from src.models import db


class TicketCategory(db.Model):
    __tablename__ = "ticket_categories"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    tickets = db.relationship("Ticket", back_populates="categoria", lazy="dynamic")

    def __repr__(self) -> str:  # pragma: no cover - representação simples
        return f"<TicketCategory {self.nome!r}>"


class TicketPriority(db.Model):
    __tablename__ = "ticket_priorities"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    peso = db.Column(db.Integer, nullable=False, default=0)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    tickets = db.relationship("Ticket", back_populates="prioridade", lazy="dynamic")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TicketPriority {self.nome!r}>"


class TicketStatus(db.Model):
    __tablename__ = "ticket_statuses"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    ordem = db.Column(db.Integer, nullable=False, default=0)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    tickets = db.relationship("Ticket", back_populates="status", lazy="dynamic")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TicketStatus {self.nome!r}>"


class TicketLocation(db.Model):
    __tablename__ = "ticket_locations"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    tickets = db.relationship("Ticket", back_populates="local", lazy="dynamic")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TicketLocation {self.nome!r}>"


class TicketAsset(db.Model):
    __tablename__ = "ticket_assets"

    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(120), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    tickets = db.relationship("Ticket", back_populates="ativo_relacionado", lazy="dynamic")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TicketAsset {self.tag!r}>"


class TicketSLA(db.Model):
    __tablename__ = "ticket_slas"
    __table_args__ = (
        UniqueConstraint(
            "categoria_id", "prioridade_id", name="uq_ticket_sla_categoria_prioridade"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("ticket_categories.id"), nullable=True)
    prioridade_id = db.Column(
        db.Integer, db.ForeignKey("ticket_priorities.id"), nullable=False
    )
    horas = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    categoria = db.relationship("TicketCategory", backref="slas")
    prioridade = db.relationship("TicketPriority", backref="slas")

    def __repr__(self) -> str:  # pragma: no cover
        alvo = self.categoria.nome if self.categoria else "*"
        return f"<TicketSLA {alvo}/{self.prioridade.nome}:{self.horas}h>"


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    categoria_id = db.Column(
        db.Integer, db.ForeignKey("ticket_categories.id"), nullable=False
    )
    prioridade_id = db.Column(
        db.Integer, db.ForeignKey("ticket_priorities.id"), nullable=False
    )
    status_id = db.Column(db.Integer, db.ForeignKey("ticket_statuses.id"), nullable=False)
    solicitante_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    atribuido_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey("ticket_locations.id"), nullable=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("ticket_assets.id"), nullable=True)
    sla_horas = db.Column(db.Integer, nullable=True)
    prazo_sla = db.Column(db.DateTime, nullable=True)
    resolvido_em = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    categoria = db.relationship("TicketCategory", back_populates="tickets")
    prioridade = db.relationship("TicketPriority", back_populates="tickets")
    status = db.relationship("TicketStatus", back_populates="tickets")
    solicitante = db.relationship(
        "User", foreign_keys=[solicitante_id], backref="tickets_criados"
    )
    atribuido = db.relationship(
        "User", foreign_keys=[atribuido_id], backref="tickets_atribuidos"
    )
    local = db.relationship("TicketLocation", back_populates="tickets")
    ativo_relacionado = db.relationship("TicketAsset", back_populates="tickets")

    comentarios = db.relationship(
        "TicketComment",
        back_populates="ticket",
        order_by="TicketComment.created_at",
        cascade="all, delete-orphan",
    )
    anexos = db.relationship(
        "TicketAttachment",
        back_populates="ticket",
        order_by="TicketAttachment.created_at",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_tickets_status_id", "status_id"),
        Index("ix_tickets_categoria_id", "categoria_id"),
        Index("ix_tickets_prioridade_id", "prioridade_id"),
        Index("ix_tickets_solicitante_id", "solicitante_id"),
        Index("ix_tickets_atribuido_id", "atribuido_id"),
        Index("ix_tickets_created_at", "created_at"),
    )

    def atualizar_resolucao(self, status_nome: Optional[str] = None) -> None:
        """Atualiza os campos de resolução baseado no status."""
        status_nome = status_nome or (self.status.nome if self.status else None)
        if status_nome in {"resolvido", "fechado"}:
            if not self.resolvido_em:
                self.resolvido_em = datetime.utcnow()
        else:
            self.resolvido_em = None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Ticket #{self.id} {self.titulo!r}>"


class TicketComment(db.Model):
    __tablename__ = "ticket_comments"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    ticket = db.relationship("Ticket", back_populates="comentarios")
    autor = db.relationship("User")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TicketComment {self.id} ticket={self.ticket_id}>"


class TicketAttachment(db.Model):
    __tablename__ = "ticket_attachments"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(120), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    ticket = db.relationship("Ticket", back_populates="anexos")
    uploader = db.relationship("User")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TicketAttachment {self.filename!r} ({self.size_bytes} bytes)>"
