"""Modelo responsável pelo armazenamento de imagens de notícias."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text

from src.models import db


def utcnow() -> datetime:
    """Retorna a data e hora atual em UTC."""

    return datetime.now(timezone.utc)


class ImagemNoticia(db.Model):
    """Representa a imagem associada a uma notícia."""

    __tablename__ = "imagens_noticias"

    id = db.Column(db.Integer, primary_key=True)
    noticia_id = db.Column(
        db.Integer,
        db.ForeignKey("noticias.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    nome_arquivo = db.Column(db.String(255), nullable=False)
    caminho_relativo = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    noticia = db.relationship("Noticia", back_populates="imagem", uselist=False)

    @property
    def url_publica(self) -> str:
        """Retorna a URL pública do arquivo armazenado."""

        caminho = self.caminho_relativo.lstrip("/")
        return f"/static/{caminho}" if caminho else None

    def to_dict(self) -> dict:
        """Serializa a imagem para um dicionário simples."""

        return {
            "id": self.id,
            "nome_arquivo": self.nome_arquivo,
            "caminho_relativo": self.caminho_relativo,
            "url": self.url_publica,
        }
