"""Rotas para o módulo de Suporte de TI."""

from __future__ import annotations

import hmac

from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError

from src.auth import admin_required, login_required
from src.schemas.support import (
    SupportKnowledgeBaseSchema,
    SupportTicketCreateSchema,
    SupportTicketUpdateSchema,
)
from src.services import support_service
from src.services.support_service import SupportServiceError
from src.utils.support_constants import VALID_STATUSES

support_bp = Blueprint("support", __name__)


def _responder_erro(mensagem: str, status_code: int = 400):
    return jsonify({"erro": mensagem}), status_code


@support_bp.before_request
def validar_csrf():
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        token_cookie = request.cookies.get("csrf_token")
        token_header = request.headers.get("X-CSRF-Token") or request.headers.get("X-CSRFToken")
        if not token_cookie or not token_header or not hmac.compare_digest(token_cookie, token_header):
            return _responder_erro("CSRF token inválido", 403)
    return None


@support_bp.route("/support/areas", methods=["GET"])
@login_required
def listar_areas():
    ativo_param = request.args.get("ativo")
    apenas_ativos = None
    if ativo_param is not None:
        ativo_normalizado = ativo_param.strip().lower()
        if ativo_normalizado in {"true", "1", "sim", "yes"}:
            apenas_ativos = True
        elif ativo_normalizado in {"false", "0", "nao", "não", "no"}:
            apenas_ativos = False
    areas = support_service.listar_areas(apenas_ativos)
    return jsonify(
        [
            {
                "id": area.id,
                "nome": area.nome,
                "descricao": area.descricao,
                "ativo": area.ativo,
            }
            for area in areas
        ]
    )


@support_bp.route("/support/equipamentos", methods=["GET"])
@login_required
def listar_equipamentos():
    ativo_param = request.args.get("ativo")
    apenas_ativos = None
    if ativo_param is not None:
        ativo_normalizado = ativo_param.strip().lower()
        if ativo_normalizado in {"true", "1", "sim", "yes"}:
            apenas_ativos = True
        elif ativo_normalizado in {"false", "0", "nao", "não", "no"}:
            apenas_ativos = False
    equipamentos = support_service.listar_tipos_equipamento(apenas_ativos)
    return jsonify(
        [
            {
                "id": equipamento.id,
                "nome": equipamento.nome,
                "descricao": equipamento.descricao,
                "ativo": equipamento.ativo,
            }
            for equipamento in equipamentos
        ]
    )


@support_bp.route("/support/tickets", methods=["POST"])
@login_required
def criar_ticket():
    dados_brutos = {chave: valor for chave, valor in request.form.items()}
    dados_brutos.setdefault("nome", g.current_user.nome)
    dados_brutos.setdefault("email", g.current_user.email)
    try:
        dados_validados = SupportTicketCreateSchema.model_validate(dados_brutos)
    except ValidationError as exc:
        return jsonify({"erros": exc.errors()}), 400

    anexos = request.files.getlist("anexos")
    try:
        ticket = support_service.criar_chamado(g.current_user.id, dados_validados, anexos)
    except SupportServiceError as exc:
        return _responder_erro(str(exc), 400)

    return jsonify(support_service.serializar_chamado(ticket)), 201


@support_bp.route("/support/tickets/mine", methods=["GET"])
@login_required
def meus_tickets():
    status = request.args.get("status")
    if status and status.lower() not in VALID_STATUSES:
        return _responder_erro(
            "Status inválido. Valores aceitos: " + ", ".join(VALID_STATUSES), 400
        )
    try:
        tickets = support_service.listar_chamados_usuario(g.current_user.id, status)
    except SupportServiceError as exc:  # pragma: no cover - atualmente não lançado
        return _responder_erro(str(exc), 400)
    return jsonify(tickets)


@support_bp.route("/support/tickets", methods=["GET"])
@admin_required
def listar_tickets_admin():
    try:
        resultado = support_service.listar_chamados_admin(
            status=request.args.get("status"),
            urgencia=request.args.get("urgencia"),
            area_id=request.args.get("area_id", type=int),
            equipamento_id=request.args.get("equipamento_id", type=int),
            ordenacao=request.args.get("ordenacao", "data"),
            ordem=request.args.get("ordem", "desc"),
            page=request.args.get("page", 1, type=int),
            per_page=request.args.get("per_page", 20, type=int),
        )
    except SupportServiceError as exc:
        return _responder_erro(str(exc), 400)
    return jsonify(resultado)


@support_bp.route("/support/tickets/<int:ticket_id>", methods=["PATCH"])
@admin_required
def atualizar_ticket(ticket_id: int):
    dados_json = request.get_json(silent=True) or {}
    try:
        dados = SupportTicketUpdateSchema.model_validate(dados_json)
    except ValidationError as exc:
        return jsonify({"erros": exc.errors()}), 400
    try:
        ticket = support_service.atualizar_chamado(ticket_id, dados)
    except SupportServiceError as exc:
        return _responder_erro(str(exc), 404 if "não encontrado" in str(exc).lower() else 400)
    return jsonify(support_service.serializar_chamado(ticket))


@support_bp.route("/support/indicadores", methods=["GET"])
@admin_required
def indicadores():
    indicadores = support_service.obter_indicadores()
    return jsonify(indicadores)


@support_bp.route("/support/areas", methods=["POST"])
@admin_required
def criar_area():
    dados_json = request.get_json(silent=True) or {}
    try:
        dados = SupportKnowledgeBaseSchema.model_validate(dados_json)
    except ValidationError as exc:
        return jsonify({"erros": exc.errors()}), 400
    try:
        area = support_service.criar_area(dados)
    except SupportServiceError as exc:
        return _responder_erro(str(exc), 400)
    return (
        jsonify({
            "id": area.id,
            "nome": area.nome,
            "descricao": area.descricao,
            "ativo": area.ativo,
        }),
        201,
    )


@support_bp.route("/support/areas/<int:area_id>", methods=["PUT"])
@admin_required
def atualizar_area(area_id: int):
    dados_json = request.get_json(silent=True) or {}
    try:
        dados = SupportKnowledgeBaseSchema.model_validate(dados_json)
    except ValidationError as exc:
        return jsonify({"erros": exc.errors()}), 400
    try:
        area = support_service.atualizar_area(area_id, dados)
    except SupportServiceError as exc:
        status_code = 404 if "não encontrada" in str(exc).lower() else 400
        return _responder_erro(str(exc), status_code)
    return jsonify({
        "id": area.id,
        "nome": area.nome,
        "descricao": area.descricao,
        "ativo": area.ativo,
    })


@support_bp.route("/support/areas/<int:area_id>", methods=["DELETE"])
@admin_required
def remover_area(area_id: int):
    try:
        support_service.remover_area(area_id)
    except SupportServiceError as exc:
        status_code = 404 if "não encontrada" in str(exc).lower() else 400
        return _responder_erro(str(exc), status_code)
    return "", 204


@support_bp.route("/support/equipamentos", methods=["POST"])
@admin_required
def criar_equipamento():
    dados_json = request.get_json(silent=True) or {}
    try:
        dados = SupportKnowledgeBaseSchema.model_validate(dados_json)
    except ValidationError as exc:
        return jsonify({"erros": exc.errors()}), 400
    try:
        equipamento = support_service.criar_tipo_equipamento(dados)
    except SupportServiceError as exc:
        return _responder_erro(str(exc), 400)
    return (
        jsonify({
            "id": equipamento.id,
            "nome": equipamento.nome,
            "descricao": equipamento.descricao,
            "ativo": equipamento.ativo,
        }),
        201,
    )


@support_bp.route("/support/equipamentos/<int:equipamento_id>", methods=["PUT"])
@admin_required
def atualizar_equipamento(equipamento_id: int):
    dados_json = request.get_json(silent=True) or {}
    try:
        dados = SupportKnowledgeBaseSchema.model_validate(dados_json)
    except ValidationError as exc:
        return jsonify({"erros": exc.errors()}), 400
    try:
        equipamento = support_service.atualizar_tipo_equipamento(equipamento_id, dados)
    except SupportServiceError as exc:
        status_code = 404 if "não encontrado" in str(exc).lower() else 400
        return _responder_erro(str(exc), status_code)
    return jsonify({
        "id": equipamento.id,
        "nome": equipamento.nome,
        "descricao": equipamento.descricao,
        "ativo": equipamento.ativo,
    })


@support_bp.route("/support/equipamentos/<int:equipamento_id>", methods=["DELETE"])
@admin_required
def remover_equipamento(equipamento_id: int):
    try:
        support_service.remover_tipo_equipamento(equipamento_id)
    except SupportServiceError as exc:
        status_code = 404 if "não encontrado" in str(exc).lower() else 400
        return _responder_erro(str(exc), status_code)
    return "", 204
