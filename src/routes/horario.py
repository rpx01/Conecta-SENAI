"""Rotas para gerenciamento de horários."""

from flask import Blueprint, request, jsonify

from src.models import db, Horario
from src.schemas.horario import HorarioCreateSchema, HorarioOutSchema
from src.services.horario_service import create_horario, update_horario

horario_bp = Blueprint("horario", __name__)


@horario_bp.route("/horarios", methods=["GET"])
def listar_horarios():
    horarios = Horario.query.order_by(Horario.nome).all()
    payload = [
        {"id": h.id, "nome": h.nome, "turno": h.turno} for h in horarios
    ]
    return jsonify(payload)


@horario_bp.route("/horarios", methods=["POST"])
def criar_horario():
    data = request.get_json(silent=True) or {}
    validated = HorarioCreateSchema(**data)
    horario = create_horario(validated.model_dump())
    out = HorarioOutSchema(
        id=horario.id, nome=horario.nome, turno=horario.turno
    )
    return jsonify(out.model_dump()), 201


@horario_bp.route("/horarios/<int:horario_id>", methods=["PUT", "PATCH"])
def atualizar_horario(horario_id: int):
    horario = db.session.get(Horario, horario_id)
    if not horario:
        return jsonify({"erro": "Horário não encontrado"}), 404
    data = request.get_json(silent=True) or {}
    payload = {
        "nome": data.get("nome", horario.nome),
        "turno": data.get("turno", horario.turno),
    }
    validated = HorarioCreateSchema(**payload)
    horario = update_horario(horario, validated.model_dump())
    out = HorarioOutSchema(
        id=horario.id, nome=horario.nome, turno=horario.turno
    )
    return jsonify(out.model_dump())


@horario_bp.route("/horarios/<int:horario_id>", methods=["DELETE"])
def excluir_horario(horario_id: int):
    horario = db.session.get(Horario, horario_id)
    if not horario:
        return jsonify({"erro": "Horário não encontrado"}), 404
    db.session.delete(horario)
    db.session.commit()
    return jsonify({"mensagem": "Horário excluído com sucesso"}), 200
