"""Rotas para apontamentos de instrutores."""
from flask import Blueprint, request, jsonify
from src.models import db
from src.models.apontamento import Apontamento
from src.routes.user import verificar_autenticacao, verificar_admin
from sqlalchemy.exc import SQLAlchemyError
from src.utils.error_handler import handle_internal_error
from pydantic import ValidationError
from src.schemas import ApontamentoCreateSchema

apontamento_bp = Blueprint('apontamento', __name__)

@apontamento_bp.route('/apontamentos', methods=['POST'])
def criar_apontamento():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    data = request.json or {}
    try:
        payload = ApontamentoCreateSchema(**data)
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400

    apont = Apontamento(
        data=payload.data,
        horas=payload.horas,
        descricao=payload.descricao,
        status=payload.status,
        instrutor_id=payload.instrutor_id,
        centro_custo_id=payload.centro_custo_id,
        ocupacao_id=payload.ocupacao_id
    )
    try:
        db.session.add(apont)
        db.session.commit()
        return jsonify(apont.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@apontamento_bp.route('/apontamentos', methods=['GET'])
def listar_apontamentos():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    apontamentos = Apontamento.query.order_by(Apontamento.data.desc()).all()
    return jsonify([a.to_dict() for a in apontamentos])
