"""Rotas para gerenciamento de horários."""
from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from src.models import db, Horario, TurnoEnum
from src.schemas.horario import HorarioCreate, HorarioUpdate, HorarioOut
from src.utils.error_handler import handle_internal_error

horario_bp = Blueprint("horario", __name__)


@horario_bp.route("/horarios", methods=["GET"])
def listar_horarios():
    """Retorna a lista de horários com seus turnos."""
    horarios = Horario.query.order_by(Horario.nome).all()
    payload = [HorarioOut.model_validate(h).model_dump() for h in horarios]
    return jsonify(payload)


@horario_bp.route("/horarios", methods=["POST"])
def criar_horario():
    data = request.get_json(silent=True) or {}
    try:
        validated = HorarioCreate(**data)
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400

    if Horario.query.filter_by(nome=validated.nome).first():
        return jsonify({"erro": "Já existe um horário com este nome"}), 400

    horario = Horario(
        nome=validated.nome,
        turno=TurnoEnum(validated.turno.value) if validated.turno else None,
    )
    db.session.add(horario)
    try:
        db.session.commit()
    except SQLAlchemyError as e:  # pragma: no cover - segurança
        db.session.rollback()
        return handle_internal_error(e)

    out = HorarioOut.model_validate(horario).model_dump()
    return jsonify(out), 201


@horario_bp.route("/horarios/<int:horario_id>", methods=["PUT", "PATCH"])
def atualizar_horario(horario_id: int):
    horario = db.session.get(Horario, horario_id)
    if not horario:
        return jsonify({"erro": "Horário não encontrado"}), 404

    data = request.get_json(silent=True) or {}
    try:
        validated = HorarioUpdate(**data)
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400

    if (
        validated.nome is not None
        and validated.nome != horario.nome
        and Horario.query.filter_by(nome=validated.nome).first()
    ):
        return jsonify({"erro": "Já existe um horário com este nome"}), 400

    if validated.nome is not None:
        horario.nome = validated.nome
    if "turno" in data:
        horario.turno = (
            TurnoEnum(validated.turno.value)
            if validated.turno is not None
            else None
        )

    try:
        db.session.commit()
    except SQLAlchemyError as e:  # pragma: no cover - segurança
        db.session.rollback()
        return handle_internal_error(e)

    out = HorarioOut.model_validate(horario).model_dump()
    return jsonify(out)


@horario_bp.route("/horarios/<int:horario_id>", methods=["DELETE"])
def excluir_horario(horario_id: int):
    horario = db.session.get(Horario, horario_id)
    if not horario:
        return jsonify({"erro": "Horário não encontrado"}), 404
    db.session.delete(horario)
    db.session.commit()
    return jsonify({"mensagem": "Horário excluído com sucesso"}), 200
