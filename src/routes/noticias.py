"""Endpoints REST do módulo de notícias."""

import hmac
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError
from sqlalchemy import or_
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError

from src.auth import admin_required
from src.models.noticia import Noticia
from src.repositories.noticia_repository import NoticiaRepository
from src.schemas.noticia import NoticiaSchema
from src.schemas.noticia_validacao import NoticiaCreateSchema, NoticiaUpdateSchema
from src.services.noticia_service import criar_noticia, atualizar_noticia, excluir_noticia
from src.utils.error_handler import handle_internal_error

log = logging.getLogger(__name__)

api_noticias_bp = Blueprint("api_noticias", __name__)

noticia_schema = NoticiaSchema()
noticias_schema = NoticiaSchema(many=True)

BOOLEAN_TRUES = {"1", "true", "t", "on", "yes", "y", "sim"}
BOOLEAN_FALSES = {"0", "false", "f", "off", "no", "n", "nao", "não"}


def _normalizar_booleano(valor: Any, default: bool | None = None) -> bool | None:
    if valor is None:
        return default
    if isinstance(valor, bool):
        return valor
    texto = str(valor).strip().lower()
    if not texto:
        return default
    if texto in BOOLEAN_TRUES:
        return True
    if texto in BOOLEAN_FALSES:
        return False
    return default


def _extrair_dados_form(expect_update: bool = False) -> Tuple[Dict[str, Any], Any]:
    if request.mimetype and "application/json" in request.mimetype:
        dados_brutos: Dict[str, Any] = request.get_json(silent=True) or {}
        arquivo = None
    else:
        dados_brutos = {chave: valor for chave, valor in request.form.items()}
        arquivo = request.files.get("imagem")

    dados_brutos.pop("csrf_token", None)
    dados_brutos.pop("csrfmiddlewaretoken", None)
    dados_brutos.pop("_method", None)

    data_agendamento = dados_brutos.pop("dataAgendamento", None) or dados_brutos.pop("data_agendamento", None)

    if "destaque" in dados_brutos:
        valor = _normalizar_booleano(dados_brutos.get("destaque"), False if not expect_update else None)
        if valor is None and expect_update:
            dados_brutos.pop("destaque", None)
        else:
            dados_brutos["destaque"] = valor if valor is not None else False
    elif not expect_update:
        dados_brutos["destaque"] = False

    if "ativo" in dados_brutos:
        valor = _normalizar_booleano(dados_brutos.get("ativo"), True if not expect_update else None)
        if valor is None and expect_update:
            dados_brutos.pop("ativo", None)
        else:
            dados_brutos["ativo"] = valor if valor is not None else True
    elif not expect_update:
        dados_brutos["ativo"] = True

    dados_brutos.pop("imagem", None)

    imagem_url = dados_brutos.get("imagem_url")
    if not expect_update:
        dados_brutos.setdefault("imagem_url", imagem_url if imagem_url is not None else None)
    else:
        dados_brutos.pop("imagem_url", None)

    data_publicacao = dados_brutos.get("dataPublicacao") or dados_brutos.pop("data_publicacao", None)
    if data_publicacao:
        dados_brutos["dataPublicacao"] = data_publicacao
    if data_agendamento:
        dados_brutos["dataAgendamento"] = data_agendamento

    return dados_brutos, arquivo


def _serialize_validation_errors(err: ValidationError) -> list[dict]:
    """Converte erros de validação do Pydantic em estruturas JSON serializáveis."""
    serialized: list[dict] = []
    for error in err.errors():
        ctx = error.get("ctx")
        if isinstance(ctx, dict):
            error = {**error, "ctx": {k: str(v) if isinstance(v, Exception) else v for k, v in ctx.items()}}
        serialized.append(error)
    return serialized


@api_noticias_bp.before_request
def proteger_csrf():
    """Valida o token CSRF em requisições mutáveis."""
    if request.method not in {"POST", "PUT", "DELETE"}:
        return None
    token_cookie = request.cookies.get("csrf_token")
    token_header = request.headers.get("X-CSRF-Token") or request.headers.get("X-CSRFToken")
    if not token_cookie or not token_header or not hmac.compare_digest(token_cookie, token_header):
        return jsonify({"erro": "CSRF token inválido"}), 403
    return None


@api_noticias_bp.route("/noticias", methods=["GET"])
def listar_noticias():
    """Lista notícias paginadas, permitindo filtros básicos."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 12, type=int)
    per_page = max(1, min(per_page, 50))
    incluir_inativas = request.args.get("include_inativas", "false").lower() == "true"
    destaque_param = request.args.get("destaque")
    status_param = request.args.get("ativo") or request.args.get("status")
    termo_busca = request.args.get("busca") or request.args.get("q")

    try:
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
            consulta = consulta.filter(
                or_(Noticia.titulo.ilike(like), Noticia.resumo.ilike(like))
            )

        consulta = consulta.order_by(Noticia.data_publicacao.desc(), Noticia.id.desc())
        paginacao = consulta.paginate(page=page, per_page=per_page, error_out=False)
        itens = noticias_schema.dump(paginacao.items)
        return jsonify(
            {
                "items": itens,
                "page": paginacao.page,
                "per_page": paginacao.per_page,
                "total": paginacao.total,
                "pages": paginacao.pages,
            }
        ), 200
    except (ProgrammingError, SQLAlchemyError) as exc:
        mensagem = str(exc).lower()
        if isinstance(exc, ProgrammingError) or "no such table" in mensagem:
            current_app.logger.error(
                "Tabela 'noticias' ausente. Rode as migrações.",
                exc_info=True,
            )
            return (
                jsonify(
                    {
                        "items": [],
                        "page": page,
                        "per_page": per_page,
                        "total": 0,
                        "pages": 0,
                    }
                ),
                200,
            )
        raise


@api_noticias_bp.route("/noticias/<int:noticia_id>", methods=["GET"])
def obter_noticia(noticia_id: int):
    """Retorna os detalhes de uma notícia específica."""
    incluir_inativas = request.args.get("include_inativas", "false").lower() == "true"
    try:
        noticia = NoticiaRepository.get_by_id(noticia_id)
    except (ProgrammingError, SQLAlchemyError) as exc:
        mensagem = str(exc).lower()
        if isinstance(exc, ProgrammingError) or "no such table" in mensagem:
            current_app.logger.error(
                "Tabela 'noticias' ausente ao buscar notícia.",
                exc_info=True,
            )
            return jsonify({"erro": "Notícia não encontrada"}), 404
        raise

    if not noticia:
        return jsonify({"erro": "Notícia não encontrada"}), 404
    if not incluir_inativas and not noticia.ativo:
        return jsonify({"erro": "Notícia não encontrada"}), 404
    try:
        return jsonify(noticia_schema.dump(noticia)), 200
    except (ProgrammingError, SQLAlchemyError) as exc:
        mensagem = str(exc).lower()
        if isinstance(exc, ProgrammingError) or "no such table" in mensagem:
            current_app.logger.error(
                "Tabela 'noticias' ausente ao buscar notícia.",
                exc_info=True,
            )
            return jsonify({"erro": "Notícia não encontrada"}), 404
        raise


@api_noticias_bp.route("/noticias", methods=["POST"])
@admin_required
def criar():
    """Cria uma nova notícia."""
    dados_brutos, arquivo_imagem = _extrair_dados_form()
    try:
        payload = NoticiaCreateSchema.model_validate(dados_brutos)
    except ValidationError as err:
        return jsonify({"erros": _serialize_validation_errors(err)}), 400

    dados = payload.model_dump(mode="python")
    data_agendamento = dados.pop("data_agendamento", None)
    if data_agendamento and not dados.get("data_publicacao"):
        dados["data_publicacao"] = data_agendamento
    if dados.get("data_publicacao") is None and dados.get("ativo", True):
        dados["data_publicacao"] = datetime.now(timezone.utc)

    try:
        noticia = criar_noticia(dados, arquivo_imagem=arquivo_imagem)
    except SQLAlchemyError as exc:  # pragma: no cover
        log.exception("Erro ao criar notícia")
        return handle_internal_error(exc)

    return jsonify(noticia_schema.dump(noticia)), 201


@api_noticias_bp.route("/noticias/<int:noticia_id>", methods=["PUT"])
@admin_required
def atualizar(noticia_id: int):
    """Atualiza os dados de uma notícia existente."""
    noticia = NoticiaRepository.get_by_id(noticia_id)
    if not noticia:
        return jsonify({"erro": "Notícia não encontrada"}), 404

    dados_brutos, arquivo_imagem = _extrair_dados_form(expect_update=True)
    try:
        payload = NoticiaUpdateSchema.model_validate(dados_brutos)
    except ValidationError as err:
        return jsonify({"erros": _serialize_validation_errors(err)}), 400

    dados = payload.model_dump(mode="python", exclude_unset=True)
    data_agendamento = dados.pop("data_agendamento", None)
    if data_agendamento is not None:
        dados["data_publicacao"] = data_agendamento

    if not dados and arquivo_imagem is None:
        return jsonify({"erro": "Nenhum dado fornecido para atualização"}), 400

    try:
        noticia_atualizada = atualizar_noticia(
            noticia,
            dados,
            arquivo_imagem=arquivo_imagem,
        )
    except SQLAlchemyError as exc:  # pragma: no cover
        log.exception("Erro ao atualizar notícia %s", noticia_id)
        return handle_internal_error(exc)

    return jsonify(noticia_schema.dump(noticia_atualizada)), 200


@api_noticias_bp.route("/noticias/<int:noticia_id>", methods=["DELETE"])
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
