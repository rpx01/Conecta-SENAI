"""Modelos relacionados ao gerenciamento de chamados de TI."""
import enum
from datetime import datetime

from src.extensions import db
from src.models.user import User


class StatusChamado(enum.Enum):
    """Enumeração que representa os possíveis status de um chamado."""

    ABERTO = "Aberto"
    EM_ANDAMENTO = "Em Andamento"
    AGUARDANDO_USUARIO = "Aguardando Usuário"
    FECHADO = "Fechado"


class TipoProblema(db.Model):
    """Categoria de um chamado."""

    __tablename__ = "tipoproblema"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=True)

    chamados = db.relationship(
        "Chamado", back_populates="tipo_problema", lazy="dynamic"
    )

    def __repr__(self) -> str:  # pragma: no cover - representação auxiliar
        return f"<TipoProblema {self.nome}>"


class Chamado(db.Model):
    """Registro de um chamado aberto por um usuário."""

    __tablename__ = "chamado"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.Enum(StatusChamado), nullable=False, default=StatusChamado.ABERTO
    )
    data_abertura = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_fechamento = db.Column(db.DateTime, nullable=True)

    solicitante_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id"), nullable=False
    )
    solicitante = db.relationship(
        "User", foreign_keys=[solicitante_id], back_populates="chamados_abertos"
    )

    tipo_problema_id = db.Column(
        db.Integer, db.ForeignKey("tipoproblema.id"), nullable=False
    )
    tipo_problema = db.relationship("TipoProblema", back_populates="chamados")

    admin_responsavel_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id"), nullable=True
    )
    admin_responsavel = db.relationship(
        "User",
        foreign_keys=[admin_responsavel_id],
        back_populates="chamados_responsaveis",
    )

    mensagens = db.relationship(
        "MensagemChamado",
        back_populates="chamado",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - representação auxiliar
        return f"<Chamado {self.id} - {self.titulo}>"


class MensagemChamado(db.Model):
    """Histórico de mensagens trocadas em um chamado."""

    __tablename__ = "mensagemchamado"

    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    data_envio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    chamado_id = db.Column(db.Integer, db.ForeignKey("chamado.id"), nullable=False)
    chamado = db.relationship("Chamado", back_populates="mensagens")

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    usuario = db.relationship("User", back_populates="mensagens_chamados")

    def __repr__(self) -> str:  # pragma: no cover - representação auxiliar
        return f"<MensagemChamado {self.id} por {self.usuario.nome}>"
