"""Job para publicação de notícias agendadas."""

import logging
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError

from src.extensions import db
from src.models.noticia import Noticia

log = logging.getLogger(__name__)


def publicar_noticias_agendadas():
    """Busca por notícias agendadas e não publicadas e as torna ativas."""
    agora = datetime.now(timezone.utc)
    noticias_para_publicar = Noticia.query.filter(
        Noticia.ativo.is_(False),
        Noticia.data_publicacao <= agora,
    ).all()

    if not noticias_para_publicar:
        log.info("Nenhuma notícia agendada para publicar no momento.")
        return

    sucesso_count = 0
    falha_count = 0

    for noticia in noticias_para_publicar:
        try:
            noticia.ativo = True
            db.session.add(noticia)
            sucesso_count += 1
        except SQLAlchemyError:
            falha_count += 1
            log.exception(
                "Falha ao tentar publicar a notícia agendada com ID %s",
                noticia.id,
            )

    if sucesso_count > 0:
        try:
            db.session.commit()
            log.info("Publicadas %d notícias agendadas com sucesso.", sucesso_count)
        except SQLAlchemyError:
            db.session.rollback()
            log.exception(
                "Erro ao commitar a publicação de notícias. Nenhuma alteração foi salva."
            )

    if falha_count > 0:
        log.warning(
            "%d notícias agendadas não puderam ser publicadas devido a erros.",
            falha_count,
        )
