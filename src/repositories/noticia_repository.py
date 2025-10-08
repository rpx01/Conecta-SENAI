"""Repositório com operações de banco para notícias."""

from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from src.models import db
from src.models.noticia import Noticia


class NoticiaRepository:
    """Encapsula o acesso ao banco para o modelo :class:`Noticia`."""

    @staticmethod
    def base_query():
        return Noticia.query

    @staticmethod
    def get_by_id(noticia_id: int) -> Optional[Noticia]:
        return db.session.get(Noticia, noticia_id)

    @staticmethod
    def add(noticia: Noticia) -> Noticia:
        db.session.add(noticia)
        db.session.commit()
        return noticia

    @staticmethod
    def delete(noticia: Noticia) -> None:
        db.session.delete(noticia)
        db.session.commit()

    @staticmethod
    def commit():
        db.session.commit()

    @staticmethod
    def rollback():  # pragma: no cover - utilitário para fluxos de erro
        db.session.rollback()

    @staticmethod
    def save(noticia: Noticia) -> Noticia:
        try:
            db.session.add(noticia)
            db.session.commit()
            return noticia
        except SQLAlchemyError:
            db.session.rollback()
            raise
