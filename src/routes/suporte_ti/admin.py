"""Rotas administrativas do módulo de suporte de TI."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from flask import Blueprint, jsonify, request
from sqlalchemy import func, inspect
from sqlalchemy.exc import SQLAlchemyError

from src.auth import admin_required
from src.models import db
from src.models.suporte_basedados import SuporteArea, SuporteTipoEquipamento
from src.models.suporte_chamado import SuporteChamado

suporte_ti_admin_bp = Blueprint(
    "suporte_ti_admin",
    __name__,
    url_prefix="/api/suporte_ti/admin",
)


def _ensure_tables_exist(models: Iterable[type[db.Model]]) -> None:
    inspector = inspect(db.engine)
    for model in models:
        if not inspector.has_table(model.__tablename__):
            model.__table__.create(db.engine)
            inspector = inspect(db.engine)


def _serialize_chamado(chamado: SuporteChamado) -> dict:
    return {
        "id": chamado.id,
        "user_id": chamado.user_id,
        "nome": chamado.user.nome if chamado.user else None,
        "email": chamado.email,
        "area": chamado.area,
        "tipo_equipamento_id": chamado.tipo_equipamento_id,
        "tipo_equipamento_nome": (
            chamado.tipo_equipamento.nome if chamado.tipo_equipamento else None
        ),
        "patrimonio": chamado.patrimonio,
        "numero_serie": chamado.numero_serie,
        "descricao_problema": chamado.descricao_problema,
        "nivel_urgencia": chamado.nivel_urgencia,
        "status": chamado.status,
        "created_at": chamado.created_at.isoformat() if chamado.created_at else None,
        "updated_at": chamado.updated_at.isoformat() if chamado.updated_at else None,
        "anexos": [anexo.file_path for anexo in chamado.anexos],
    }


@suporte_ti_admin_bp.route("/todos_chamados", methods=["GET"])
@admin_required
def listar_todos_chamados():
    _ensure_tables_exist([SuporteChamado])
    consulta = SuporteChamado.query

    status_param = request.args.get("status")
    if status_param:
        status_lista = [valor.strip() for valor in status_param.split(",") if valor.strip()]
        if status_lista:
            consulta = consulta.filter(SuporteChamado.status.in_(status_lista))

    area_param = request.args.get("area")
    if area_param:
        consulta = consulta.filter(SuporteChamado.area == area_param)

    tipo_param = request.args.get("tipo_equipamento_id") or request.args.get(
        "tipoEquipamentoId"
    )
    if tipo_param:
        try:
            tipo_id = int(tipo_param)
            consulta = consulta.filter(SuporteChamado.tipo_equipamento_id == tipo_id)
        except ValueError:
            return jsonify({"erro": "Parâmetro tipo_equipamento_id inválido"}), 400

    urgencia_param = request.args.get("nivel_urgencia")
    if urgencia_param:
        consulta = consulta.filter(SuporteChamado.nivel_urgencia == urgencia_param)

    data_inicio = request.args.get("data_inicio") or request.args.get("dataInicio")
    data_fim = request.args.get("data_fim") or request.args.get("dataFim")

    def _parse_data(valor: str | None) -> datetime | None:
        if not valor:
            return None
        try:
            return datetime.fromisoformat(valor)
        except ValueError:
            try:
                return datetime.strptime(valor, "%Y-%m-%d")
            except ValueError:
                return None

    inicio = _parse_data(data_inicio)
    fim = _parse_data(data_fim)

    if data_inicio and inicio is None:
        return jsonify({"erro": "data_inicio inválida"}), 400
    if data_fim and fim is None:
        return jsonify({"erro": "data_fim inválida"}), 400

    if inicio is not None:
        consulta = consulta.filter(SuporteChamado.created_at >= inicio)
    if fim is not None:
        consulta = consulta.filter(SuporteChamado.created_at <= fim)

    consulta = consulta.order_by(SuporteChamado.created_at.desc())
    chamados = consulta.all()
    return jsonify([_serialize_chamado(chamado) for chamado in chamados])


@suporte_ti_admin_bp.route("/indicadores", methods=["GET"])
@admin_required
def obter_indicadores():
    _ensure_tables_exist([SuporteChamado])

    total = db.session.query(func.count(SuporteChamado.id)).scalar() or 0
    por_status = (
        db.session.query(SuporteChamado.status, func.count(SuporteChamado.id))
        .group_by(SuporteChamado.status)
        .all()
    )
    por_tipo = (
        db.session.query(SuporteTipoEquipamento.nome, func.count(SuporteChamado.id))
        .join(
            SuporteTipoEquipamento,
            SuporteTipoEquipamento.id == SuporteChamado.tipo_equipamento_id,
            isouter=True,
        )
        .group_by(SuporteTipoEquipamento.nome)
        .all()
    )
    por_urgencia = (
        db.session.query(SuporteChamado.nivel_urgencia, func.count(SuporteChamado.id))
        .group_by(SuporteChamado.nivel_urgencia)
        .all()
    )

    return jsonify(
        {
            "total_chamados": total,
            "por_status": [
                {"status": status or "Não informado", "quantidade": quantidade}
                for status, quantidade in por_status
            ],
            "por_tipo_equipamento": [
                {"tipo": tipo or "Não informado", "quantidade": quantidade}
                for tipo, quantidade in por_tipo
            ],
            "por_nivel_urgencia": [
                {"nivel": nivel or "Não informado", "quantidade": quantidade}
                for nivel, quantidade in por_urgencia
            ],
        }
    )


def _criar_registro_basico(model, nome: str):
    if not nome.strip():
        return None, "Nome é obrigatório."
    existente = model.query.filter(func.lower(model.nome) == nome.strip().lower()).first()
    if existente:
        return None, "Registro já cadastrado."
    registro = model(nome=nome.strip())
    try:
        db.session.add(registro)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return None, "Erro ao salvar registro."
    return registro, None


def _atualizar_registro_basico(model, registro_id: int, nome: str):
    registro = db.session.get(model, registro_id)
    if not registro:
        return None, "Registro não encontrado."
    if not nome.strip():
        return None, "Nome é obrigatório."
    conflito = (
        model.query.filter(func.lower(model.nome) == nome.strip().lower(), model.id != registro_id)
        .first()
    )
    if conflito:
        return None, "Registro já cadastrado."
    registro.nome = nome.strip()
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return None, "Erro ao atualizar registro."
    return registro, None


def _excluir_registro_basico(model, registro_id: int):
    registro = db.session.get(model, registro_id)
    if not registro:
        return False, "Registro não encontrado."
    try:
        db.session.delete(registro)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return False, "Erro ao excluir registro."
    return True, None


@suporte_ti_admin_bp.route("/tipos_equipamento", methods=["GET"])
@admin_required
def listar_tipos_equipamento():
    _ensure_tables_exist([SuporteTipoEquipamento])
    tipos = SuporteTipoEquipamento.query.order_by(SuporteTipoEquipamento.nome.asc()).all()
    return jsonify([{"id": tipo.id, "nome": tipo.nome} for tipo in tipos])


@suporte_ti_admin_bp.route("/tipos_equipamento", methods=["POST"])
@admin_required
def criar_tipo_equipamento():
    _ensure_tables_exist([SuporteTipoEquipamento])
    payload = request.get_json(silent=True) or {}
    nome = payload.get("nome", "")
    registro, erro = _criar_registro_basico(SuporteTipoEquipamento, nome)
    if erro:
        return jsonify({"erro": erro}), 400 if "salvar" not in erro.lower() else 500
    return jsonify({"id": registro.id, "nome": registro.nome}), 201


@suporte_ti_admin_bp.route("/tipos_equipamento/<int:registro_id>", methods=["PUT"])
@admin_required
def atualizar_tipo_equipamento(registro_id: int):
    _ensure_tables_exist([SuporteTipoEquipamento])
    payload = request.get_json(silent=True) or {}
    nome = payload.get("nome", "")
    registro, erro = _atualizar_registro_basico(SuporteTipoEquipamento, registro_id, nome)
    if erro:
        status = 404 if "não encontrado" in erro.lower() else 400
        if "atualizar" in erro.lower():
            status = 500
        return jsonify({"erro": erro}), status
    return jsonify({"id": registro.id, "nome": registro.nome})


@suporte_ti_admin_bp.route("/tipos_equipamento/<int:registro_id>", methods=["DELETE"])
@admin_required
def excluir_tipo_equipamento(registro_id: int):
    _ensure_tables_exist([SuporteTipoEquipamento])
    sucesso, erro = _excluir_registro_basico(SuporteTipoEquipamento, registro_id)
    if erro:
        status = 404 if "não encontrado" in erro.lower() else 500
        return jsonify({"erro": erro}), status
    return jsonify({"mensagem": "Tipo de equipamento removido com sucesso."})


@suporte_ti_admin_bp.route("/areas", methods=["GET"])
@admin_required
def listar_areas():
    _ensure_tables_exist([SuporteArea])
    areas = SuporteArea.query.order_by(SuporteArea.nome.asc()).all()
    return jsonify([{"id": area.id, "nome": area.nome} for area in areas])


@suporte_ti_admin_bp.route("/areas", methods=["POST"])
@admin_required
def criar_area():
    _ensure_tables_exist([SuporteArea])
    payload = request.get_json(silent=True) or {}
    nome = payload.get("nome", "")
    registro, erro = _criar_registro_basico(SuporteArea, nome)
    if erro:
        return jsonify({"erro": erro}), 400 if "salvar" not in erro.lower() else 500
    return jsonify({"id": registro.id, "nome": registro.nome}), 201


@suporte_ti_admin_bp.route("/areas/<int:registro_id>", methods=["PUT"])
@admin_required
def atualizar_area(registro_id: int):
    _ensure_tables_exist([SuporteArea])
    payload = request.get_json(silent=True) or {}
    nome = payload.get("nome", "")
    registro, erro = _atualizar_registro_basico(SuporteArea, registro_id, nome)
    if erro:
        status = 404 if "não encontrado" in erro.lower() else 400
        if "atualizar" in erro.lower():
            status = 500
        return jsonify({"erro": erro}), status
    return jsonify({"id": registro.id, "nome": registro.nome})


@suporte_ti_admin_bp.route("/areas/<int:registro_id>", methods=["DELETE"])
@admin_required
def excluir_area(registro_id: int):
    _ensure_tables_exist([SuporteArea])
    sucesso, erro = _excluir_registro_basico(SuporteArea, registro_id)
    if erro:
        status = 404 if "não encontrado" in erro.lower() else 500
        return jsonify({"erro": erro}), status
    return jsonify({"mensagem": "Área removida com sucesso."})
