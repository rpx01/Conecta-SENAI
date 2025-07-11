"""Rotas para apontamentos de instrutores."""
from flask import Blueprint, request, jsonify
from sqlalchemy import extract
from src.models import db
from src.models.apontamento import Apontamento
from src.models.instrutor import Instrutor
from src.models.centro_custo import CentroCusto
from src.routes.user import verificar_autenticacao, verificar_admin
from sqlalchemy.exc import SQLAlchemyError
from src.utils.error_handler import handle_internal_error

apontamento_bp = Blueprint('apontamento', __name__)

@apontamento_bp.route('/apontamentos', methods=['POST'])
def criar_apontamento():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    data = request.json or {}
    instrutor_id = data.get('instrutor_id') or user.id
    if not verificar_admin(user) and instrutor_id != user.id:
        return jsonify({'erro': 'Permissão negada'}), 403
    instrutor = db.session.get(Instrutor, instrutor_id)
    centro = db.session.get(CentroCusto, data.get('centro_custo_id'))
    if not instrutor or not centro:
        return jsonify({'erro': 'Dados inválidos'}), 400
    try:
        apont = Apontamento(
            data=data.get('data'),
            horas=data.get('horas'),
            descricao=data.get('descricao'),
            instrutor_id=instrutor_id,
            centro_custo_id=centro.id,
        )
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
    query = Apontamento.query
    if not verificar_admin(user):
        query = query.filter(Apontamento.instrutor_id == user.id)
    apontamentos = query.order_by(Apontamento.data.desc()).all()
    return jsonify([a.to_dict() for a in apontamentos])

@apontamento_bp.route('/apontamentos/<int:apontamento_id>', methods=['PUT'])
def atualizar_status(apontamento_id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado or not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    apont = db.session.get(Apontamento, apontamento_id)
    if not apont:
        return jsonify({'erro': 'Apontamento não encontrado'}), 404
    status = (request.json or {}).get('status')
    if status:
        apont.status = status
    try:
        db.session.commit()
        return jsonify(apont.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)
