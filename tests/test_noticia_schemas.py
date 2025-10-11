"""Testes para os esquemas de validação de notícias."""

from datetime import datetime, timezone

import pytest

from src.schemas.noticia_validacao import NoticiaCreateSchema


def test_noticia_create_schema_accepts_isoformat_with_z_suffix():
    """Garante que datas com sufixo ``Z`` sejam aceitas e convertidas para UTC."""

    payload = {
        "titulo": "Notícia com data em UTC",
        "resumo": "Um resumo válido com tamanho suficiente.",
        "conteudo": "Um conteúdo válido com mais de vinte caracteres.",
        "dataPublicacao": "2025-10-09T13:30:14.000Z",
    }

    schema = NoticiaCreateSchema.model_validate(payload)

    assert schema.data_publicacao == datetime(2025, 10, 9, 13, 30, 14, tzinfo=timezone.utc)


def test_noticia_create_schema_parses_data_evento():
    """Garante que a data do evento seja convertida para UTC ao marcar no calendário."""

    payload = {
        "titulo": "Notícia com evento",
        "resumo": "Resumo válido com tamanho adequado.",
        "conteudo": "Conteúdo suficientemente longo para validação.",
        "marcarCalendario": True,
        "dataEvento": "2025-05-01T08:00:00Z",
    }

    schema = NoticiaCreateSchema.model_validate(payload)

    assert schema.marcar_calendario is True
    assert schema.data_evento == datetime(2025, 5, 1, 8, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "valor",
    ["2025-10-09 13:30:14", "2025-10-09T13:30:14", "2025-10-09T13:30:14+00:00"],
)
def test_noticia_create_schema_normalizes_naive_datetimes(valor):
    """Datas válidas são normalizadas para UTC quando não há informação de timezone."""

    payload = {
        "titulo": "Notícia com data normalizada",
        "resumo": "Resumo suficiente para passar na validação.",
        "conteudo": "Conteúdo válido com caracteres suficientes para validação.",
        "dataPublicacao": valor,
    }

    schema = NoticiaCreateSchema.model_validate(payload)

    assert schema.data_publicacao.tzinfo == timezone.utc

