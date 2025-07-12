"""Rotas para centros de custo."""
from flask import Blueprint, request, jsonify
from src.models import db
from src.models.centro_custo import CentroCusto
from src.routes.user import verificar_autenticacao, verificar_admin
from sqlalchemy.exc import SQLAlchemyError
from src.utils.error_handler import handle_internal_error
from pydantic import ValidationError
from src.schemas import CentroCustoCreateSchema, CentroCustoUpdateSchema

centro_custo_bp = Blueprint('centro_custo', __name__)

@centro_custo_bp.route('/centros-custo', methods=['GET'])
def listar_centros_custo():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    centros = CentroCusto.query.order_by(CentroCusto.nome).all()
    return jsonify([c.to_dict() for c in centros])

@centro_custo_bp.route('/centros-custo', methods=['POST'])
def criar_centro_custo():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    data = request.json or {}
    try:
        payload = CentroCustoCreateSchema(**data)
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400

    novo = CentroCusto(nome=payload.nome, descricao=payload.descricao, ativo=payload.ativo)
    try:
        db.session.add(novo)
        db.session.commit()
        return jsonify(novo.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@centro_custo_bp.route('/centros-custo/<int:id>', methods=['PUT'])
def atualizar_centro_custo(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    centro = db.session.get(CentroCusto, id)
    if not centro:
        return jsonify({'erro': 'Centro de custo não encontrado'}), 404

    data = request.json or {}
    try:
        payload = CentroCustoUpdateSchema(**data)
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400

    if payload.nome is not None:
        centro.nome = payload.nome
    if payload.descricao is not None:
        centro.descricao = payload.descricao
    if payload.ativo is not None:
        centro.ativo = payload.ativo

    try:
        db.session.commit()
        return jsonify(centro.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@centro_custo_bp.route('/centros-custo/<int:id>', methods=['DELETE'])
def remover_centro_custo(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    centro = db.session.get(CentroCusto, id)
    if not centro:
        return jsonify({'erro': 'Centro de custo não encontrado'}), 404

    try:
        db.session.delete(centro)
        db.session.commit()
        return jsonify({'mensagem': 'Removido com sucesso'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)
