from flask import Blueprint, request, jsonify
from src.models import db
from src.models.centro_custo import CentroCusto
from src.auth import admin_required

centro_custo_bp = Blueprint('centro_custo', __name__)

@centro_custo_bp.route('/centros-custo', methods=['GET'])
@admin_required
def listar_centros_custo():
    centros = CentroCusto.query.all()
    return jsonify([c.to_dict() for c in centros])

@centro_custo_bp.route('/centros-custo/<int:id>', methods=['GET'])
@admin_required
def obter_centro_custo(id):
    centro = db.session.get(CentroCusto, id)
    if not centro:
        return jsonify({'erro': 'Centro de custo não encontrado'}), 404
    return jsonify(centro.to_dict())

@centro_custo_bp.route('/centros-custo', methods=['POST'])
@admin_required
def criar_centro_custo():
    data = request.get_json() or {}
    if not data.get('nome'):
        return jsonify({'erro': 'Nome é obrigatório'}), 400
    centro = CentroCusto(data['nome'], data.get('descricao'), data.get('ativo', True))
    db.session.add(centro)
    db.session.commit()
    return jsonify(centro.to_dict()), 201

@centro_custo_bp.route('/centros-custo/<int:id>', methods=['PUT'])
@admin_required
def atualizar_centro_custo(id):
    centro = db.session.get(CentroCusto, id)
    if not centro:
        return jsonify({'erro': 'Centro de custo não encontrado'}), 404
    data = request.get_json() or {}
    centro.nome = data.get('nome', centro.nome)
    centro.descricao = data.get('descricao', centro.descricao)
    if 'ativo' in data:
        centro.ativo = data['ativo']
    db.session.commit()
    return jsonify(centro.to_dict())

@centro_custo_bp.route('/centros-custo/<int:id>', methods=['DELETE'])
@admin_required
def remover_centro_custo(id):
    centro = db.session.get(CentroCusto, id)
    if not centro:
        return jsonify({'erro': 'Centro de custo não encontrado'}), 404
    db.session.delete(centro)
    db.session.commit()
    return jsonify({'mensagem': 'Centro de custo removido'})
