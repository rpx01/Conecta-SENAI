"""Job para publicação de notícias agendadas."""

import logging

from src.services.noticia_service import publicar_noticias_agendadas as _publicar_noticias_agendadas

log = logging.getLogger(__name__)


def publicar_noticias_agendadas() -> dict[str, int]:
    """Executa a publicação de notícias agendadas com registro em log."""

    resultado = _publicar_noticias_agendadas()

    if resultado["total"] == 0:
        return resultado

    if resultado["publicadas"]:
        log.info(
            "Publicadas %d notícias agendadas com sucesso.",
            resultado["publicadas"],
        )

    if resultado["falhas"]:
        log.warning(
            "%d notícias agendadas não puderam ser publicadas devido a erros.",
            resultado["falhas"],
        )

    return resultado
