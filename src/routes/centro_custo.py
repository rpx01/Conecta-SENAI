from flask import Blueprint, request, jsonify
from src.models import db
from src.models.centro_custo import CentroCusto
from src.routes.user import verificar_autenticacao, verificar_admin
from sqlalchemy.exc import SQLAlchemyError
from src.utils.error_handler import handle_internal_error

centro_custo_bp = Blueprint('centro_custo', __name__)

@centro_custo_bp.route('/centros-custo', methods=['GET'])
def listar_centros():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    centros = CentroCusto.query.order_by(CentroCusto.nome).all()
    return jsonify([c.to_dict() for c in centros])

@centro_custo_bp.route('/centros-custo', methods=['POST'])
def criar_centro():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    data = request.json or {}
    if not data.get('nome'):
        return jsonify({'erro': 'Nome é obrigatório'}), 400
    try:
        centro = CentroCusto(nome=data['nome'], descricao=data.get('descricao'), ativo=data.get('ativo', True))
        db.session.add(centro)
        db.session.commit()
        return jsonify(centro.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@centro_custo_bp.route('/centros-custo/<int:id>', methods=['PUT'])
def atualizar_centro(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    centro = db.session.get(CentroCusto, id)
    if not centro:
        return jsonify({'erro': 'Centro não encontrado'}), 404
    data = request.json or {}
    if 'nome' in data and data['nome']:
        centro.nome = data['nome']
    if 'descricao' in data:
        centro.descricao = data['descricao']
    if 'ativo' in data:
        centro.ativo = bool(data['ativo'])
    try:
        db.session.commit()
        return jsonify(centro.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@centro_custo_bp.route('/centros-custo/<int:id>', methods=['DELETE'])
def remover_centro(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    centro = db.session.get(CentroCusto, id)
    if not centro:
        return jsonify({'erro': 'Centro não encontrado'}), 404
    try:
        db.session.delete(centro)
        db.session.commit()
        return jsonify({'mensagem': 'Centro removido'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)
