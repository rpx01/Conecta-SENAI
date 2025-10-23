"""Rotas do módulo de chamados de TI."""
from __future__ import annotations

from typing import Optional

from flask import Blueprint, Response, g, jsonify, render_template, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import SQLAlchemyError

from src.auth import admin_required, login_required, verificar_admin
from src.extensions import limiter
from src.models import (
    TicketAttachment,
    TicketAsset,
    TicketCategory,
    TicketLocation,
    TicketPriority,
    TicketSLA,
    TicketStatus,
    User,
    db,
)
from src.schemas.chamados import (
    AssetSchema,
    CategoriaSchema,
    LocationSchema,
    PrioridadeSchema,
    SLASchema,
    StatusSchema,
    TicketCommentCreateSchema,
    TicketCommentSchema,
    TicketCreateSchema,
    TicketSchema,
    TicketUpdateSchema,
)
from src.services import chamados_service
from src.services.chamados_service import resolve_attachment_path
from src.utils.error_handler import handle_internal_error

chamados_bp = Blueprint("chamados", __name__, template_folder="../templates")
chamados_api_bp = Blueprint("chamados_api", __name__)


# ---------------------------------------------------------------------------
# Páginas HTML
# ---------------------------------------------------------------------------


@chamados_bp.route("/novo")
@login_required
def pagina_novo() -> str:
    return render_template("chamados/novo.html")


@chamados_bp.route("/minhas")
@login_required
def pagina_minhas() -> str:
    return render_template("chamados/minhas.html")


@chamados_bp.route("/<int:ticket_id>")
@login_required
def pagina_detalhe(ticket_id: int) -> str:
    return render_template("chamados/detalhe.html", ticket_id=ticket_id)


@chamados_bp.route("/admin/abertos")
@admin_required
def pagina_admin_abertos() -> str:
    return render_template("chamados/admin_abertos.html")


@chamados_bp.route("/admin/indicadores")
@admin_required
def pagina_admin_indicadores() -> str:
    return render_template("chamados/admin_indicadores.html")


@chamados_bp.route("/admin/base-dados")
@admin_required
def pagina_admin_base() -> str:
    return render_template("chamados/admin_base_dados.html")


# ---------------------------------------------------------------------------
# API Helpers
# ---------------------------------------------------------------------------


def _json_error(message: str, status: int = 400) -> Response:
    request_id = getattr(g, "request_id", None)
    payload = {"erro": message}
    if request_id:
        payload["request_id"] = request_id
    return jsonify(payload), status


def _get_current_user_id() -> int:
    identidade = get_jwt_identity()
    if identidade is None:
        raise ValueError("Token inválido")
    return int(identidade)


# ---------------------------------------------------------------------------
# API de Tickets
# ---------------------------------------------------------------------------


@chamados_api_bp.route("/api/chamados", methods=["POST"])
@jwt_required()
@limiter.limit("5 per minute")
def api_criar_ticket():
    try:
        data = TicketCreateSchema().load(request.form or request.json or {})
    except Exception as err:
        return _json_error(str(err))
    try:
        arquivos = request.files.getlist("anexos")
        ticket = chamados_service.create_ticket(_get_current_user_id(), data, arquivos)
    except ValueError as err:
        db.session.rollback()
        return _json_error(str(err))
    except SQLAlchemyError as err:
        db.session.rollback()
        return handle_internal_error(err)
    return jsonify(TicketSchema().dump(ticket)), 201


@chamados_api_bp.route("/api/chamados", methods=["GET"])
@jwt_required()
def api_listar_tickets():
    user_id = _get_current_user_id()
    filtros = {
        "status_id": request.args.get("status_id", type=int),
        "categoria_id": request.args.get("categoria_id", type=int),
        "prioridade_id": request.args.get("prioridade_id", type=int),
        "q": request.args.get("q", type=str),
    }
    paginacao = {
        "page": request.args.get("page", type=int),
        "page_size": request.args.get("page_size", type=int),
    }
    mine = request.args.get("mine", "true").lower() == "true"
    try:
        if mine:
            resultado = chamados_service.list_my_tickets(user_id, filtros, paginacao)
        else:
            user = db.session.get(User, user_id)
            if not user or not verificar_admin(user):
                return _json_error("Permissão negada", 403)
            resultado = chamados_service.admin_list_open_tickets(filtros, paginacao)
    except ValueError as err:
        return _json_error(str(err))
    return jsonify(resultado)


@chamados_api_bp.route("/api/chamados/<int:ticket_id>", methods=["GET"])
@jwt_required()
def api_detalhe(ticket_id: int):
    try:
        ticket = chamados_service.get_ticket_detail(_get_current_user_id(), ticket_id)
    except PermissionError as err:
        return _json_error(str(err), 403)
    except ValueError as err:
        return _json_error(str(err), 404)
    return jsonify(TicketSchema().dump(ticket))


@chamados_api_bp.route("/api/chamados/<int:ticket_id>/comentarios", methods=["POST"])
@jwt_required()
def api_comentar(ticket_id: int):
    try:
        dados = TicketCommentCreateSchema().load(request.get_json() or {})
    except Exception as err:
        return _json_error(str(err))
    try:
        comentario = chamados_service.add_comment(
            _get_current_user_id(), ticket_id, dados["mensagem"]
        )
    except PermissionError as err:
        return _json_error(str(err), 403)
    except ValueError as err:
        return _json_error(str(err))
    return jsonify(TicketCommentSchema().dump(comentario)), 201


@chamados_api_bp.route("/api/chamados/<int:ticket_id>/anexos", methods=["POST"])
@jwt_required()
@limiter.limit("5 per minute")
def api_adicionar_anexos(ticket_id: int):
    arquivos = request.files.getlist("anexos")
    try:
        anexos = chamados_service.add_attachments(_get_current_user_id(), ticket_id, arquivos)
    except PermissionError as err:
        return _json_error(str(err), 403)
    except ValueError as err:
        return _json_error(str(err))
    return jsonify(TicketSchema().dump(chamados_service.get_ticket_detail(_get_current_user_id(), ticket_id)))


@chamados_api_bp.route(
    "/api/chamados/<int:ticket_id>/download/<int:attachment_id>",
    methods=["GET"],
)
@jwt_required()
def api_download(ticket_id: int, attachment_id: int):
    try:
        ticket = chamados_service.get_ticket_detail(_get_current_user_id(), ticket_id)
    except PermissionError as err:
        return _json_error(str(err), 403)
    except ValueError as err:
        return _json_error(str(err), 404)
    attachment = next((a for a in ticket.anexos if a.id == attachment_id), None)
    if not attachment:
        return _json_error("Anexo não encontrado", 404)
    path = resolve_attachment_path(attachment)
    if not path:
        return _json_error("Arquivo não disponível", 404)
    return send_file(path, as_attachment=True, download_name=attachment.filename)


# ---------------------------------------------------------------------------
# API Administrativa
# ---------------------------------------------------------------------------


@chamados_api_bp.route("/api/chamados/abertos", methods=["GET"])
@jwt_required()
def api_admin_abertos():
    user_id = _get_current_user_id()
    user = db.session.get(User, user_id)
    if not user or not verificar_admin(user):
        return _json_error("Permissão negada", 403)
    filtros = {
        "status_id": request.args.get("status_id", type=int),
        "categoria_id": request.args.get("categoria_id", type=int),
        "prioridade_id": request.args.get("prioridade_id", type=int),
        "atribuido_id": request.args.get("atribuido_id", type=int),
        "q": request.args.get("q", type=str),
    }
    paginacao = {
        "page": request.args.get("page", type=int),
        "page_size": request.args.get("page_size", type=int),
    }
    return jsonify(chamados_service.admin_list_open_tickets(filtros, paginacao))


@chamados_api_bp.route("/api/chamados/<int:ticket_id>", methods=["PATCH"])
@jwt_required()
def api_atualizar_ticket(ticket_id: int):
    user_id = _get_current_user_id()
    user = db.session.get(User, user_id)
    if not user or not verificar_admin(user):
        return _json_error("Permissão negada", 403)
    try:
        dados = TicketUpdateSchema().load(request.get_json() or {})
    except Exception as err:
        return _json_error(str(err))

    try:
        if dados.get("atribuido_id"):
            chamados_service.assign_ticket(user_id, ticket_id, dados["atribuido_id"])
        if dados.get("status_id"):
            chamados_service.update_status(user_id, ticket_id, dados["status_id"])
        if dados.get("prioridade_id"):
            chamados_service.update_priority(user_id, ticket_id, dados["prioridade_id"])
    except PermissionError as err:
        db.session.rollback()
        return _json_error(str(err), 403)
    except ValueError as err:
        db.session.rollback()
        return _json_error(str(err))
    return jsonify(TicketSchema().dump(chamados_service.get_ticket_detail(user_id, ticket_id)))


@chamados_api_bp.route("/api/chamados/indicadores", methods=["GET"])
@jwt_required()
def api_indicadores():
    user_id = _get_current_user_id()
    user = db.session.get(User, user_id)
    if not user or not verificar_admin(user):
        return _json_error("Permissão negada", 403)
    periodo = request.args.get("periodo", default=30, type=int)
    return jsonify(chamados_service.compute_indicators(periodo))


# ---------------------------------------------------------------------------
# CRUD Base de Dados
# ---------------------------------------------------------------------------


def _crud_list(model, schema):
    itens = model.query.order_by(model.id.asc()).all()
    return jsonify(schema(many=True).dump(itens))


def _crud_create(model, schema, payload):
    dados = schema().load(payload)
    entidade = model(**dados)
    db.session.add(entidade)
    db.session.commit()
    return jsonify(schema().dump(entidade)), 201


def _crud_patch(model, schema, entidade_id, payload):
    dados = schema(partial=True).load(payload)
    entidade = db.session.get(model, entidade_id)
    if not entidade:
        return _json_error("Registro não encontrado", 404)
    for campo, valor in dados.items():
        setattr(entidade, campo, valor)
    db.session.commit()
    return jsonify(schema().dump(entidade))


def _crud_delete(model, entidade_id, rel_field: Optional[str] = None):
    entidade = db.session.get(model, entidade_id)
    if not entidade:
        return _json_error("Registro não encontrado", 404)
    if rel_field and getattr(entidade, rel_field).count():
        return _json_error("Registro em uso", 400)
    db.session.delete(entidade)
    db.session.commit()
    return "", 204


@chamados_api_bp.route("/api/chamados/base/categorias", methods=["GET", "POST"])
@jwt_required()
def api_categorias():
    user_id = _get_current_user_id()
    user = db.session.get(User, user_id)
    if not user or not verificar_admin(user):
        return _json_error("Permissão negada", 403)
    if request.method == "GET":
        return _crud_list(TicketCategory, CategoriaSchema)
    return _crud_create(TicketCategory, CategoriaSchema, request.get_json() or {})


@chamados_api_bp.route("/api/chamados/base/categorias/<int:item_id>", methods=["PATCH", "DELETE"])
@jwt_required()
def api_categoria_item(item_id: int):
    user_id = _get_current_user_id()
    user = db.session.get(User, user_id)
    if not user or not verificar_admin(user):
        return _json_error("Permissão negada", 403)
    if request.method == "PATCH":
        return _crud_patch(TicketCategory, CategoriaSchema, item_id, request.get_json() or {})
    return _crud_delete(TicketCategory, item_id, "tickets")


@chamados_api_bp.route("/api/chamados/base/prioridades", methods=["GET", "POST"])
@jwt_required()
def api_prioridades():
    user_id = _get_current_user_id()
    user = db.session.get(User, user_id)
    if not user or not verificar_admin(user):
        return _json_error("Permissão negada", 403)
    if request.method == "GET":
        return _crud_list(TicketPriority, PrioridadeSchema)
    return _crud_create(TicketPriority, PrioridadeSchema, request.get_json() or {})


@chamados_api_bp.route("/api/chamados/base/prioridades/<int:item_id>", methods=["PATCH", "DELETE"])
@jwt_required()
def api_prioridade_item(item_id: int):
    user_id = _get_current_user_id()
    user = db.session.get(User, user_id)
    if not user or not verificar_admin(user):
        return _json_error("Permissão negada", 403)
    if request.method == "PATCH":
        return _crud_patch(TicketPriority, PrioridadeSchema, item_id, request.get_json() or {})
    return _crud_delete(TicketPriority, item_id, "tickets")


@chamados_api_bp.route("/api/chamados/base/statuses", methods=["GET", "POST"])
@jwt_required()
def api_statuses():
    user_id = _get_current_user_id()
    user = db.session.get(User, user_id)
    if not user or not verificar_admin(user):
        return _json_error("Permissão negada", 403)
    if request.method == "GET":
        return _crud_list(TicketStatus, StatusSchema)
    return _crud_create(TicketStatus, StatusSchema, request.get_json() or {})


@chamados_api_bp.route("/api/chamados/base/statuses/<int:item_id>", methods=["PATCH", "DELETE"])
@jwt_required()
def api_status_item(item_id: int):
    user_id = _get_current_user_id()
    user = db.session.get(User, user_id)
    if not user or not verificar_admin(user):
        return _json_error("Permissão negada", 403)
    if request.method == "PATCH":
        return _crud_patch(TicketStatus, StatusSchema, item_id, request.get_json() or {})
    return _crud_delete(TicketStatus, item_id, "tickets")


@chamados_api_bp.route("/api/chamados/base/locations", methods=["GET", "POST"])
@jwt_required()
def api_locations():
    user_id = _get_current_user_id()
    user = db.session.get(User, user_id)
    if not user or not verificar_admin(user):
        return _json_error("Permissão negada", 403)
    if request.method == "GET":
        return _crud_list(TicketLocation, LocationSchema)
    return _crud_create(TicketLocation, LocationSchema, request.get_json() or {})


@chamados_api_bp.route("/api/chamados/base/locations/<int:item_id>", methods=["PATCH", "DELETE"])
@jwt_required()
def api_location_item(item_id: int):
    user_id = _get_current_user_id()
    user = db.session.get(User, user_id)
    if not user or not verificar_admin(user):
        return _json_error("Permissão negada", 403)
    if request.method == "PATCH":
        return _crud_patch(TicketLocation, LocationSchema, item_id, request.get_json() or {})
    return _crud_delete(TicketLocation, item_id, "tickets")


@chamados_api_bp.route("/api/chamados/base/assets", methods=["GET", "POST"])
@jwt_required()
def api_assets():
    user_id = _get_current_user_id()
    user = db.session.get(User, user_id)
    if not user or not verificar_admin(user):
        return _json_error("Permissão negada", 403)
    if request.method == "GET":
        return _crud_list(TicketAsset, AssetSchema)
    return _crud_create(TicketAsset, AssetSchema, request.get_json() or {})


@chamados_api_bp.route("/api/chamados/base/assets/<int:item_id>", methods=["PATCH", "DELETE"])
@jwt_required()
def api_asset_item(item_id: int):
    user_id = _get_current_user_id()
    user = db.session.get(User, user_id)
    if not user or not verificar_admin(user):
        return _json_error("Permissão negada", 403)
    if request.method == "PATCH":
        return _crud_patch(TicketAsset, AssetSchema, item_id, request.get_json() or {})
    return _crud_delete(TicketAsset, item_id, "tickets")


@chamados_api_bp.route("/api/chamados/base/slas", methods=["GET", "POST"])
@jwt_required()
def api_slas():
    user_id = _get_current_user_id()
    user = db.session.get(User, user_id)
    if not user or not verificar_admin(user):
        return _json_error("Permissão negada", 403)
    if request.method == "GET":
        return _crud_list(TicketSLA, SLASchema)
    return _crud_create(TicketSLA, SLASchema, request.get_json() or {})


@chamados_api_bp.route("/api/chamados/base/slas/<int:item_id>", methods=["PATCH", "DELETE"])
@jwt_required()
def api_sla_item(item_id: int):
    user_id = _get_current_user_id()
    user = db.session.get(User, user_id)
    if not user or not verificar_admin(user):
        return _json_error("Permissão negada", 403)
    if request.method == "PATCH":
        return _crud_patch(TicketSLA, SLASchema, item_id, request.get_json() or {})
    return _crud_delete(TicketSLA, item_id)


__all__ = ["chamados_bp", "chamados_api_bp"]
