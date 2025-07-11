"""Rotas para centros de custo."""
from flask import Blueprint, request, jsonify
from src.models import db
from src.models.centro_custo import CentroCusto
from src.routes.user import verificar_autenticacao, verificar_admin
from sqlalchemy.exc import SQLAlchemyError
from src.utils.error_handler import handle_internal_error

centro_custo_bp = Blueprint('centro_custo', __name__)

@centro_custo_bp.route('/centros-custo', methods=['GET'])
def listar_centros_custo():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado or not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    centros = CentroCusto.query.all()
    return jsonify([c.to_dict() for c in centros])

@centro_custo_bp.route('/centros-custo', methods=['POST'])
def criar_centro_custo():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado or not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    data = request.json or {}
    nome = data.get('nome')
    if not nome:
        return jsonify({'erro': 'Nome é obrigatório'}), 400
    if CentroCusto.query.filter_by(nome=nome).first():
        return jsonify({'erro': 'Centro de custo já existe'}), 400
    centro = CentroCusto(nome=nome, descricao=data.get('descricao'), ativo=data.get('ativo', True))
    try:
        db.session.add(centro)
        db.session.commit()
        return jsonify(centro.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@centro_custo_bp.route('/centros-custo/<int:id>', methods=['PUT'])
def atualizar_centro_custo(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado or not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    centro = db.session.get(CentroCusto, id)
    if not centro:
        return jsonify({'erro': 'Centro de custo não encontrado'}), 404
    data = request.json or {}
    if 'nome' in data:
        nome = data['nome']
        if nome and nome != centro.nome and CentroCusto.query.filter_by(nome=nome).first():
            return jsonify({'erro': 'Nome já utilizado'}), 400
        centro.nome = nome or centro.nome
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
def remover_centro_custo(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado or not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    centro = db.session.get(CentroCusto, id)
    if not centro:
        return jsonify({'erro': 'Centro de custo não encontrado'}), 404
    try:
        db.session.delete(centro)
        db.session.commit()
        return jsonify({'mensagem': 'Removido'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)
