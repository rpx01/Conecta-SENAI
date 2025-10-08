"""Endpoints REST do módulo de notícias."""

import hmac
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from src.auth import admin_required
from src.models.noticia import Noticia
from src.repositories.noticia_repository import NoticiaRepository
from src.schemas.noticia import NoticiaCreateSchema, NoticiaUpdateSchema
from src.services.noticia_service import criar_noticia, atualizar_noticia, excluir_noticia
from src.utils.error_handler import handle_internal_error

log = logging.getLogger(__name__)

noticias_api_bp = Blueprint("noticias_api", __name__)


@noticias_api_bp.before_request
def proteger_csrf():
    """Valida o token CSRF em requisições mutáveis."""
    if request.method not in {"POST", "PUT", "DELETE"}:
        return None
    token_cookie = request.cookies.get("csrf_token")
    token_header = request.headers.get("X-CSRF-Token") or request.headers.get("X-CSRFToken")
    if not token_cookie or not token_header or not hmac.compare_digest(token_cookie, token_header):
        return jsonify({"erro": "CSRF token inválido"}), 403
    return None


@noticias_api_bp.route("/noticias", methods=["GET"])
def listar_noticias():
    """Lista notícias paginadas, permitindo filtros básicos."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 12, type=int)
    per_page = max(1, min(per_page, 50))
    incluir_inativas = request.args.get("include_inativas", "false").lower() == "true"
    destaque_param = request.args.get("destaque")
    status_param = request.args.get("ativo") or request.args.get("status")
    termo_busca = request.args.get("busca") or request.args.get("q")

    consulta = NoticiaRepository.base_query()
    if status_param:
        status_normalizado = status_param.lower()
        if status_normalizado in {"true", "1", "ativos", "publicado", "publicada"}:
            consulta = consulta.filter(Noticia.ativo.is_(True))
        elif status_normalizado in {"false", "0", "inativos", "rascunho", "desativado"}:
            consulta = consulta.filter(Noticia.ativo.is_(False))
    elif not incluir_inativas:
        consulta = consulta.filter(Noticia.ativo.is_(True))
    if destaque_param:
        destaque_normalizado = destaque_param.lower()
        if destaque_normalizado in {"true", "1", "sim", "destaque"}:
            consulta = consulta.filter(Noticia.destaque.is_(True))
        elif destaque_normalizado in {"false", "0", "nao", "não", "comum"}:
            consulta = consulta.filter(Noticia.destaque.is_(False))
    if termo_busca:
        like = f"%{termo_busca}%"
        consulta = consulta.filter(or_(Noticia.titulo.ilike(like), Noticia.resumo.ilike(like)))

    consulta = consulta.order_by(Noticia.data_publicacao.desc(), Noticia.id.desc())
    paginacao = consulta.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        {
            "items": [noticia.to_dict() for noticia in paginacao.items],
            "page": paginacao.page,
            "per_page": paginacao.per_page,
            "total": paginacao.total,
            "pages": paginacao.pages,
        }
    )


@noticias_api_bp.route("/noticias/<int:noticia_id>", methods=["GET"])
def obter_noticia(noticia_id: int):
    """Retorna os detalhes de uma notícia específica."""
    incluir_inativas = request.args.get("include_inativas", "false").lower() == "true"
    noticia = NoticiaRepository.get_by_id(noticia_id)
    if not noticia:
        return jsonify({"erro": "Notícia não encontrada"}), 404
    if not incluir_inativas and not noticia.ativo:
        return jsonify({"erro": "Notícia não encontrada"}), 404
    return jsonify(noticia.to_dict())


@noticias_api_bp.route("/noticias", methods=["POST"])
@admin_required
def criar():
    """Cria uma nova notícia."""
    try:
        payload = NoticiaCreateSchema.model_validate(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"erros": err.errors()}), 400

    dados = payload.model_dump(mode="python")
    if not dados.get("data_publicacao"):
        dados["data_publicacao"] = datetime.utcnow()

    try:
        noticia = criar_noticia(dados)
    except SQLAlchemyError as exc:  # pragma: no cover
        log.exception("Erro ao criar notícia")
        return handle_internal_error(exc)

    return jsonify(noticia.to_dict()), 201


@noticias_api_bp.route("/noticias/<int:noticia_id>", methods=["PUT"])
@admin_required
def atualizar(noticia_id: int):
    """Atualiza os dados de uma notícia existente."""
    noticia = NoticiaRepository.get_by_id(noticia_id)
    if not noticia:
        return jsonify({"erro": "Notícia não encontrada"}), 404

    try:
        payload = NoticiaUpdateSchema.model_validate(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"erros": err.errors()}), 400

    dados = payload.model_dump(mode="python", exclude_unset=True)
    if not dados:
        return jsonify({"erro": "Nenhum dado fornecido para atualização"}), 400

    try:
        noticia_atualizada = atualizar_noticia(noticia, dados)
    except SQLAlchemyError as exc:  # pragma: no cover
        log.exception("Erro ao atualizar notícia %s", noticia_id)
        return handle_internal_error(exc)

    return jsonify(noticia_atualizada.to_dict())


@noticias_api_bp.route("/noticias/<int:noticia_id>", methods=["DELETE"])
@admin_required
def remover(noticia_id: int):
    """Remove uma notícia."""
    noticia = NoticiaRepository.get_by_id(noticia_id)
    if not noticia:
        return jsonify({"erro": "Notícia não encontrada"}), 404

    try:
        excluir_noticia(noticia)
    except SQLAlchemyError as exc:  # pragma: no cover
        log.exception("Erro ao remover notícia %s", noticia_id)
        return handle_internal_error(exc)

    return "", 204
