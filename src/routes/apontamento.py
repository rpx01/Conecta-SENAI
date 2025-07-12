from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from datetime import date

from src.models import db
from src.models.apontamento import Apontamento
from src.models.instrutor import Instrutor
from src.models.centro_custo import CentroCusto
from src.auth import login_required, admin_required
from src.utils.error_handler import handle_internal_error

apontamento_bp = Blueprint('apontamento', __name__)

@apontamento_bp.route('/apontamentos', methods=['GET'])
@login_required
def listar_apontamentos():
    apontamentos = Apontamento.query.all()
    return jsonify([a.to_dict() for a in apontamentos])

@apontamento_bp.route('/apontamentos/<int:id>', methods=['GET'])
@login_required
def obter_apontamento(id):
    apontamento = db.session.get(Apontamento, id)
    if not apontamento:
        return jsonify({'erro': 'Apontamento não encontrado'}), 404
    return jsonify(apontamento.to_dict())

@apontamento_bp.route('/apontamentos', methods=['POST'])
@admin_required
def criar_apontamento():
    data = request.json or {}
    campos = ['data', 'horas', 'descricao', 'instrutor_id', 'centro_custo_id']
    if not all(c in data for c in campos):
        return jsonify({'erro': 'Dados incompletos'}), 400
    try:
        apontamento = Apontamento(
            data=date.fromisoformat(data['data']),
            horas=data['horas'],
            descricao=data['descricao'],
            status=data.get('status', 'Pendente'),
            instrutor_id=data['instrutor_id'],
            centro_custo_id=data['centro_custo_id'],
            ocupacao_id=data.get('ocupacao_id')
        )
        db.session.add(apontamento)
        db.session.commit()
        return jsonify(apontamento.to_dict()), 201
    except (ValueError, SQLAlchemyError) as e:
        db.session.rollback()
        return handle_internal_error(e)

@apontamento_bp.route('/apontamentos/<int:id>', methods=['PUT'])
@admin_required
def atualizar_apontamento(id):
    apontamento = db.session.get(Apontamento, id)
    if not apontamento:
        return jsonify({'erro': 'Apontamento não encontrado'}), 404
    data = request.json or {}
    if 'data' in data:
        try:
            apontamento.data = date.fromisoformat(data['data'])
        except ValueError:
            return jsonify({'erro': 'Data inválida'}), 400
    if 'horas' in data:
        apontamento.horas = data['horas']
    if 'descricao' in data:
        apontamento.descricao = data['descricao']
    if 'status' in data:
        apontamento.status = data['status']
    if 'instrutor_id' in data:
        apontamento.instrutor_id = data['instrutor_id']
    if 'centro_custo_id' in data:
        apontamento.centro_custo_id = data['centro_custo_id']
    if 'ocupacao_id' in data:
        apontamento.ocupacao_id = data['ocupacao_id']
    try:
        db.session.commit()
        return jsonify(apontamento.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@apontamento_bp.route('/apontamentos/<int:id>', methods=['DELETE'])
@admin_required
def remover_apontamento(id):
    apontamento = db.session.get(Apontamento, id)
    if not apontamento:
        return jsonify({'erro': 'Apontamento não encontrado'}), 404
    try:
        db.session.delete(apontamento)
        db.session.commit()
        return jsonify({'mensagem': 'Apontamento removido com sucesso'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)
