"""Rotas para gerenciamento de horários baseados em turnos."""

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from src.models import db, Horario
from src.schemas.horario import HorarioIn, HorarioOut
from src.services.horario_service import create_horario, update_horario

horario_bp = Blueprint("horario", __name__)


@horario_bp.route("/horarios", methods=["POST"])
def criar_horario():
    dados = request.get_json() or {}
    try:
        payload = HorarioIn.model_validate(dados)
    except ValidationError as exc:
        return jsonify({"erros": exc.errors()}), 400

    horario = create_horario(payload.model_dump())
    return HorarioOut.model_validate(horario).model_dump(), 201


@horario_bp.route("/horarios/<int:horario_id>", methods=["PUT"])
def atualizar_horario(horario_id: int):
    horario = db.session.get(Horario, horario_id)
    if not horario:
        return jsonify({"erro": "Horário não encontrado"}), 404

    dados = request.get_json() or {}
    try:
        payload = HorarioIn.model_validate(dados)
    except ValidationError as exc:
        return jsonify({"erros": exc.errors()}), 400

    horario_atualizado = update_horario(horario, payload.model_dump())
    return HorarioOut.model_validate(horario_atualizado).model_dump()


@horario_bp.route("/horarios", methods=["GET"])
def listar_horarios():
    horarios = Horario.query.order_by(Horario.id).all()
    return [HorarioOut.model_validate(h).model_dump() for h in horarios]
