from datetime import datetime
from flask import Blueprint, request, jsonify, g
from src.models import db
from src.models.apontamento import Apontamento
from src.auth import login_required
from src.routes.user import verificar_admin

apontamento_bp = Blueprint('apontamento', __name__)

@apontamento_bp.route('/apontamentos', methods=['GET'])
@login_required
def listar_apontamentos():
    user = g.current_user
    if verificar_admin(user):
        apontamentos = Apontamento.query.all()
    else:
        apontamentos = Apontamento.query.filter_by(instrutor_id=user.id).all()
    return jsonify([a.to_dict() for a in apontamentos])

@apontamento_bp.route('/apontamentos', methods=['POST'])
@login_required
def criar_apontamento():
    user = g.current_user
    data = request.get_json() or {}
    try:
        ap = Apontamento(
            data=data.get('data'),
            horas=data.get('horas'),
            descricao=data.get('descricao'),
            status=data.get('status', 'pendente'),
            instrutor_id=data.get('instrutor_id') if verificar_admin(user) else user.id,
            centro_custo_id=data.get('centro_custo_id'),
            ocupacao_id=data.get('ocupacao_id')
        )
        db.session.add(ap)
        db.session.commit()
        return jsonify(ap.to_dict()), 201
    except Exception:
        db.session.rollback()
        return jsonify({'erro': 'Dados inválidos'}), 400
