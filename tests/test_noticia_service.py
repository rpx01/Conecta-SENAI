"""Testes para o módulo de regras de negócio de notícias."""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import current_app
from sqlalchemy import text
from sqlalchemy.orm.attributes import LoaderCallableStatus
from werkzeug.datastructures import FileStorage

from src.models import db
from src.models.noticia import Noticia
from src.services import noticia_service


def test_atualizar_noticia_quando_tabela_imagens_indisponivel(app, tmp_path):
    """Garante que a atualização persiste apenas o caminho quando a tabela não existe."""

    with app.app_context():
        # Remove a tabela de imagens para simular ambientes ainda não migrados.
        with db.engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS imagens_noticias"))

        # Força o serviço a reavaliar a disponibilidade da tabela.
        noticia_service._TABELA_IMAGENS_DISPONIVEL = None

        noticia = Noticia(titulo="Titulo teste", conteudo="Conteudo teste")
        db.session.add(noticia)
        db.session.commit()

        current_app.static_folder = tmp_path.as_posix()

        arquivo = FileStorage(stream=io.BytesIO(b"dados"), filename="imagem.png")

        noticia = Noticia.query.get(noticia.id)
        atualizada = noticia_service.atualizar_noticia(noticia, {}, arquivo)

        assert atualizada.imagem_url is not None
        assert atualizada.imagem_url.startswith("/static/uploads/noticias/")

        caminho_relativo = atualizada.imagem_url.replace("/static/", "", 1)
        caminho_final = Path(current_app.static_folder) / caminho_relativo

        assert caminho_final.exists()

        # A tabela continua indisponível e a relação não deve ser carregada.
        assert noticia_service._TABELA_IMAGENS_DISPONIVEL is False
        assert db.inspect(atualizada).attrs.imagem.loaded_value is LoaderCallableStatus.NO_VALUE


def test_publicar_noticias_agendadas_altera_status_para_ativo(app):
    with app.app_context():
        db.create_all()

        agora = datetime.now(timezone.utc)
        noticia_agendada = Noticia(
            titulo="Notícia agendada",
            conteudo="Conteúdo agendado para publicação automática." * 1,
            ativo=False,
            data_publicacao=agora - timedelta(minutes=10),
        )
        noticia_futura = Noticia(
            titulo="Notícia futura",
            conteudo="Conteúdo ainda não deve ser publicado automaticamente." * 1,
            ativo=False,
            data_publicacao=agora + timedelta(minutes=10),
        )

        db.session.add_all([noticia_agendada, noticia_futura])
        db.session.commit()

        resultado = noticia_service.publicar_noticias_agendadas()

        publicada = db.session.get(Noticia, noticia_agendada.id)
        pendente = db.session.get(Noticia, noticia_futura.id)

        assert resultado == {"total": 1, "publicadas": 1, "falhas": 0}
        assert publicada.ativo is True
        assert pendente.ativo is False
