"""Regras de negócio para o módulo de notícias."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple
from uuid import uuid4

from flask import current_app
from sqlalchemy import inspect
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from src.models import db
from src.models.imagem_noticia import ImagemNoticia
from src.models.noticia import Noticia
from src.repositories.noticia_repository import NoticiaRepository

UPLOAD_SUBDIR = Path("uploads") / "noticias"

_TABELA_IMAGENS_DISPONIVEL: bool | None = None


def _obter_pasta_upload() -> Path:
    static_folder = Path(current_app.static_folder)
    pasta = static_folder / UPLOAD_SUBDIR
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _gerar_nome_arquivo(arquivo: FileStorage) -> str:
    nome_seguro = secure_filename(arquivo.filename or "")
    extensao = Path(nome_seguro).suffix
    return f"{uuid4().hex}{extensao}" if extensao else uuid4().hex


def _salvar_arquivo_imagem(arquivo: FileStorage) -> Tuple[str, str]:
    pasta = _obter_pasta_upload()
    nome_arquivo = _gerar_nome_arquivo(arquivo)
    caminho_absoluto = pasta / nome_arquivo
    arquivo.save(caminho_absoluto)
    caminho_relativo = (UPLOAD_SUBDIR / nome_arquivo).as_posix()
    return nome_arquivo, caminho_relativo


def _remover_arquivo(caminho_relativo: str | None) -> None:
    if not caminho_relativo:
        return
    static_folder = Path(current_app.static_folder).resolve()
    try:
        caminho = (static_folder / caminho_relativo).resolve()
    except FileNotFoundError:
        return
    if static_folder not in caminho.parents and caminho != static_folder:
        return
    try:
        caminho.unlink(missing_ok=True)
    except TypeError:  # Python < 3.8 compatibility
        if caminho.exists():
            caminho.unlink()
    except OSError:
        current_app.logger.warning(
            "Não foi possível remover o arquivo de imagem %s", caminho, exc_info=True
        )


def _registrar_tabela_imagens_indisponivel(exc: Exception | None = None) -> None:
    global _TABELA_IMAGENS_DISPONIVEL
    _TABELA_IMAGENS_DISPONIVEL = False
    if exc:
        current_app.logger.debug(
            "Tabela 'imagens_noticias' indisponível: %s", exc, exc_info=False
        )


def _tabela_imagens_disponivel(force_refresh: bool = False) -> bool:
    global _TABELA_IMAGENS_DISPONIVEL
    if _TABELA_IMAGENS_DISPONIVEL is not None and not force_refresh:
        return _TABELA_IMAGENS_DISPONIVEL

    try:
        bind = db.session.get_bind()
    except SQLAlchemyError:
        bind = None

    if bind is None:
        bind = db.engine

    try:
        inspector = inspect(bind)
        resultado = inspector.has_table(ImagemNoticia.__tablename__)
    except SQLAlchemyError as exc:  # pragma: no cover - introspecção defensiva
        _registrar_tabela_imagens_indisponivel(exc)
        return False

    _TABELA_IMAGENS_DISPONIVEL = resultado
    return resultado


def _extrair_caminho_relativo_de_url(url: str | None) -> str | None:
    if not url:
        return None
    prefixo = "/static/"
    if url.startswith(prefixo):
        return url[len(prefixo) :]
    return url.lstrip("/")


def _construir_url_publica(caminho_relativo: str | None) -> str | None:
    if not caminho_relativo:
        return None
    caminho = caminho_relativo.lstrip("/")
    if not caminho:
        return None
    return f"/static/{caminho}"


def _carregar_imagem_relacionada(
    noticia: Noticia,
) -> Tuple[ImagemNoticia | None, str | None, bool]:
    tabela_disponivel = _tabela_imagens_disponivel()
    imagem_relacionada: ImagemNoticia | None = None
    caminho_relativo: str | None = None

    if tabela_disponivel:
        try:
            imagem_relacionada = getattr(noticia, "imagem", None)
        except (ProgrammingError, SQLAlchemyError) as exc:
            _registrar_tabela_imagens_indisponivel(exc)
            tabela_disponivel = False
        else:
            if imagem_relacionada is not None:
                caminho_relativo = getattr(imagem_relacionada, "caminho_relativo", None)

    if caminho_relativo is None:
        caminho_relativo = _extrair_caminho_relativo_de_url(getattr(noticia, "imagem_url", None))

    return imagem_relacionada, caminho_relativo, tabela_disponivel


def _aplicar_imagem(noticia: Noticia, arquivo: FileStorage | None) -> Tuple[str | None, str | None]:
    """Aplica uma nova imagem à notícia e retorna o caminho removido."""

    if not arquivo or not arquivo.filename:
        return None, None

    nome_arquivo, caminho_relativo = _salvar_arquivo_imagem(arquivo)
    imagem_relacionada, caminho_antigo, tabela_disponivel = _carregar_imagem_relacionada(noticia)

    if tabela_disponivel and imagem_relacionada is not None:
        imagem_relacionada.nome_arquivo = nome_arquivo
        imagem_relacionada.caminho_relativo = caminho_relativo
        noticia.imagem_url = imagem_relacionada.url_publica
        return caminho_antigo, caminho_relativo

    if tabela_disponivel:
        try:
            noticia.imagem = ImagemNoticia(
                nome_arquivo=nome_arquivo,
                caminho_relativo=caminho_relativo,
            )
        except (ProgrammingError, SQLAlchemyError) as exc:
            _registrar_tabela_imagens_indisponivel(exc)
        else:
            noticia.imagem_url = noticia.imagem.url_publica
            return caminho_antigo, caminho_relativo

    noticia.imagem = None
    noticia.imagem_url = _construir_url_publica(caminho_relativo)
    current_app.logger.debug(
        "Persistindo caminho da imagem no campo 'imagem_url' por indisponibilidade da tabela 'imagens_noticias'."
    )
    return caminho_antigo, caminho_relativo


def criar_noticia(dados: Dict[str, Any], arquivo_imagem: FileStorage | None = None) -> Noticia:
    """Persiste uma nova notícia validada."""

    caminho_salvo = None
    noticia = Noticia(**dados)
    try:
        if arquivo_imagem and arquivo_imagem.filename:
            _, caminho_salvo = _aplicar_imagem(noticia, arquivo_imagem)
        noticia = NoticiaRepository.add(noticia)
        return noticia
    except SQLAlchemyError as exc:  # pragma: no cover - erros de banco são delegados
        NoticiaRepository.rollback()
        if caminho_salvo:
            _remover_arquivo(caminho_salvo)
        raise exc


def atualizar_noticia(
    noticia: Noticia,
    dados: Dict[str, Any],
    arquivo_imagem: FileStorage | None = None,
) -> Noticia:
    """Atualiza a notícia informada com os dados fornecidos."""

    caminho_antigo = None
    caminho_novo = None
    if arquivo_imagem and arquivo_imagem.filename:
        caminho_antigo, caminho_novo = _aplicar_imagem(noticia, arquivo_imagem)

    for campo, valor in dados.items():
        setattr(noticia, campo, valor)

    try:
        NoticiaRepository.commit()
        if caminho_antigo and caminho_antigo != caminho_novo:
            _remover_arquivo(caminho_antigo)
        return noticia
    except SQLAlchemyError as exc:  # pragma: no cover
        NoticiaRepository.rollback()
        if caminho_novo:
            _remover_arquivo(caminho_novo)
        raise exc


def excluir_noticia(noticia: Noticia) -> None:
    """Remove a notícia do banco de dados."""

    _, caminho_antigo, _ = _carregar_imagem_relacionada(noticia)
    try:
        NoticiaRepository.delete(noticia)
        if caminho_antigo:
            _remover_arquivo(caminho_antigo)
    except SQLAlchemyError as exc:  # pragma: no cover
        NoticiaRepository.rollback()
        raise exc
