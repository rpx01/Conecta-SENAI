"""Regras de negócio para o módulo de notícias."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple
from uuid import uuid4

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from src.models.imagem_noticia import ImagemNoticia
from src.models.noticia import Noticia
from src.repositories.noticia_repository import NoticiaRepository

UPLOAD_SUBDIR = Path("uploads") / "noticias"


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


def _aplicar_imagem(noticia: Noticia, arquivo: FileStorage | None) -> Tuple[str | None, str | None]:
    """Aplica uma nova imagem à notícia e retorna o caminho removido."""

    if not arquivo or not arquivo.filename:
        return None, None

    nome_arquivo, caminho_relativo = _salvar_arquivo_imagem(arquivo)
    caminho_antigo = noticia.imagem.caminho_relativo if noticia.imagem else None

    if noticia.imagem:
        noticia.imagem.nome_arquivo = nome_arquivo
        noticia.imagem.caminho_relativo = caminho_relativo
    else:
        noticia.imagem = ImagemNoticia(
            nome_arquivo=nome_arquivo,
            caminho_relativo=caminho_relativo,
        )
    noticia.imagem_url = noticia.imagem.url_publica
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

    caminho_antigo = noticia.imagem.caminho_relativo if noticia.imagem else None
    try:
        NoticiaRepository.delete(noticia)
        if caminho_antigo:
            _remover_arquivo(caminho_antigo)
    except SQLAlchemyError as exc:  # pragma: no cover
        NoticiaRepository.rollback()
        raise exc
