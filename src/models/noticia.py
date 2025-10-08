"""Modelo de dados para notícias institucionais."""

from datetime import datetime
from sqlalchemy import text

from src.models import db


class Noticia(db.Model):
    """Representa uma notícia publicada no portal."""

    __tablename__ = "noticias"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    resumo = db.Column(db.String(400), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    autor = db.Column(db.String(120), nullable=True)
    imagem_url = db.Column(db.String(500), nullable=True)
    destaque = db.Column(db.Boolean, nullable=False, default=False, server_default=text("false"))
    ativo = db.Column(db.Boolean, nullable=False, default=True, server_default=text("true"))
    data_publicacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict:
        """Serializa a instância para dicionário pronto para JSON."""
        return {
            "id": self.id,
            "titulo": self.titulo,
            "resumo": self.resumo,
            "conteudo": self.conteudo,
            "autor": self.autor,
            "imagem_url": self.imagem_url,
            "destaque": bool(self.destaque),
            "ativo": bool(self.ativo),
            "data_publicacao": self.data_publicacao.isoformat() if self.data_publicacao else None,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - representação auxiliar
        return f"<Noticia {self.id} - {self.titulo!r}>"
