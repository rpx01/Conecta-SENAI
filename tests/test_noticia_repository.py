from sqlalchemy import inspect

from src.models import db
from src.models.noticia import Noticia
from src.repositories.noticia_repository import NoticiaRepository


def _drop_noticias_table(engine):
    inspector = inspect(engine)
    if inspector.has_table(Noticia.__tablename__):
        Noticia.__table__.drop(engine)


def test_ensure_table_exists_creates_table_when_missing(app):
    with app.app_context():
        engine = db.engine
        _drop_noticias_table(engine)

        inspector = inspect(engine)
        assert not inspector.has_table(Noticia.__tablename__)

        assert NoticiaRepository.ensure_table_exists(force_refresh=True)
        assert inspect(engine).has_table(Noticia.__tablename__)


def test_add_after_automatic_table_creation(app):
    with app.app_context():
        engine = db.engine
        _drop_noticias_table(engine)
        NoticiaRepository.ensure_table_exists(force_refresh=True)

        noticia = Noticia(titulo="Titulo", conteudo="Conteudo")
        criada = NoticiaRepository.add(noticia)

        assert criada.id is not None
        assert inspect(engine).has_table(Noticia.__tablename__)
