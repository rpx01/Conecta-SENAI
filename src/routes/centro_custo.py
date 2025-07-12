from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError

from src.models import db
from src.models.centro_custo import CentroCusto
from src.auth import login_required, admin_required
from src.utils.error_handler import handle_internal_error

centro_custo_bp = Blueprint('centro_custo', __name__)

@centro_custo_bp.route('/centros-custo', methods=['GET'])
@login_required
def listar_centros():
    centros = CentroCusto.query.all()
    return jsonify([c.to_dict() for c in centros])

@centro_custo_bp.route('/centros-custo/<int:id>', methods=['GET'])
@login_required
def obter_centro(id):
    centro = db.session.get(CentroCusto, id)
    if not centro:
        return jsonify({'erro': 'Centro de Custo não encontrado'}), 404
    return jsonify(centro.to_dict())

@centro_custo_bp.route('/centros-custo', methods=['POST'])
@admin_required
def criar_centro():
    data = request.json or {}
    nome = data.get('nome')
    if not nome:
        return jsonify({'erro': 'Nome é obrigatório'}), 400
    if CentroCusto.query.filter_by(nome=nome).first():
        return jsonify({'erro': 'Nome já existe'}), 400
    centro = CentroCusto(
        nome=nome,
        descricao=data.get('descricao'),
        ativo=data.get('ativo', True)
    )
    try:
        db.session.add(centro)
        db.session.commit()
        return jsonify(centro.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@centro_custo_bp.route('/centros-custo/<int:id>', methods=['PUT'])
@admin_required
def atualizar_centro(id):
    centro = db.session.get(CentroCusto, id)
    if not centro:
        return jsonify({'erro': 'Centro de Custo não encontrado'}), 404
    data = request.json or {}
    if 'nome' in data:
        if not data['nome']:
            return jsonify({'erro': 'Nome não pode estar vazio'}), 400
        existente = CentroCusto.query.filter_by(nome=data['nome']).first()
        if existente and existente.id != id:
            return jsonify({'erro': 'Já existe outro centro com este nome'}), 400
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
@admin_required
def remover_centro(id):
    centro = db.session.get(CentroCusto, id)
    if not centro:
        return jsonify({'erro': 'Centro de Custo não encontrado'}), 404
    try:
        db.session.delete(centro)
        db.session.commit()
        return jsonify({'mensagem': 'Centro de Custo removido com sucesso'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)
