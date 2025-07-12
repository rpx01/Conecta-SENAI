from flask import Blueprint, request, jsonify
from src.models import db
from src.models.apontamento import Apontamento
from src.routes.user import verificar_autenticacao, verificar_admin
from sqlalchemy.exc import SQLAlchemyError
from src.utils.error_handler import handle_internal_error

apontamento_bp = Blueprint('apontamento', __name__)

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

@apontamento_bp.route('/apontamentos', methods=['POST'])
def criar_apontamento():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    data = request.json or {}
    try:
        data_reg = data.get('data')
        if isinstance(data_reg, str):
            from datetime import datetime
            data_reg = datetime.strptime(data_reg, '%Y-%m-%d').date()
        ap = Apontamento(
            data=data_reg,
            horas=data.get('horas'),
            descricao=data.get('descricao'),
            status=data.get('status', 'pendente'),
            instrutor_id=data.get('instrutor_id'),
            centro_custo_id=data.get('centro_custo_id'),
            ocupacao_id=data.get('ocupacao_id')
        )
        db.session.add(ap)
        db.session.commit()
        return jsonify(ap.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)
