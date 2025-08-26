"""Rotas para gerenciamento de horários."""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from src.models import db, Horario
from src.schemas.horario import HorarioCreate, HorarioUpdate, HorarioRead
from src.services.horario_service import create_horario, update_horario

horario_bp = Blueprint('horario', __name__)


@horario_bp.route('/horarios', methods=['GET'])
def listar_horarios():
    horarios = Horario.query.order_by(Horario.nome).all()
    return jsonify(
        [HorarioRead.model_validate(h).model_dump() for h in horarios]
    )


@horario_bp.route('/horarios', methods=['POST'])
def criar_horario():
    try:
        data = HorarioCreate(**(request.get_json() or {}))
    except ValidationError as err:
        return jsonify({'erro': err.errors()}), 422
    horario = create_horario(data)
    return jsonify(HorarioRead.model_validate(horario).model_dump()), 201


@horario_bp.route('/horarios/<int:horario_id>', methods=['PUT', 'PATCH'])
def atualizar_horario(horario_id: int):
    horario = db.session.get(Horario, horario_id)
    if not horario:
        return jsonify({'erro': 'Horário não encontrado'}), 404
    try:
        data = HorarioUpdate(**(request.get_json() or {}))
    except ValidationError as err:
        return jsonify({'erro': err.errors()}), 422
    horario = update_horario(horario, data)
    return jsonify(HorarioRead.model_validate(horario).model_dump())


@horario_bp.route('/horarios/<int:horario_id>', methods=['DELETE'])
def excluir_horario(horario_id: int):
    horario = db.session.get(Horario, horario_id)
    if not horario:
        return jsonify({'erro': 'Horário não encontrado'}), 404
    db.session.delete(horario)
    db.session.commit()
    return jsonify({'mensagem': 'Horário excluído com sucesso'}), 200
