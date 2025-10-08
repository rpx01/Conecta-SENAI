"""Regras de negócio para o módulo de notícias."""

from typing import Dict, Any

from sqlalchemy.exc import SQLAlchemyError

from src.models.noticia import Noticia
from src.repositories.noticia_repository import NoticiaRepository


def criar_noticia(dados: Dict[str, Any]) -> Noticia:
    """Persiste uma nova notícia validada."""
    try:
        noticia = Noticia(**dados)
        return NoticiaRepository.add(noticia)
    except SQLAlchemyError as exc:  # pragma: no cover - erros de banco são delegados
        NoticiaRepository.rollback()
        raise exc


def atualizar_noticia(noticia: Noticia, dados: Dict[str, Any]) -> Noticia:
    """Atualiza a notícia informada com os dados fornecidos."""
    for campo, valor in dados.items():
        setattr(noticia, campo, valor)
    try:
        NoticiaRepository.commit()
        return noticia
    except SQLAlchemyError as exc:  # pragma: no cover
        NoticiaRepository.rollback()
        raise exc


def excluir_noticia(noticia: Noticia) -> None:
    """Remove a notícia do banco de dados."""
    try:
        NoticiaRepository.delete(noticia)
    except SQLAlchemyError as exc:  # pragma: no cover
        NoticiaRepository.rollback()
        raise exc
