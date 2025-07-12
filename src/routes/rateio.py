from flask import Blueprint, request, jsonify
from src.models import db
from src.models.apontamento import Apontamento
from src.routes.user import verificar_autenticacao, verificar_admin
from sqlalchemy import func

rateio_bp = Blueprint('rateio', __name__)

@rateio_bp.route('/rateio/relatorio', methods=['GET'])
def relatorio_rateio():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado or not verificar_admin(user):
        return jsonify({'erro': 'Não autorizado'}), 403
    inicio = request.args.get('inicio')
    fim = request.args.get('fim')
    query = db.session.query(func.sum(Apontamento.horas).label('total'))
    if inicio:
        query = query.filter(Apontamento.data >= inicio)
    if fim:
        query = query.filter(Apontamento.data <= fim)
    total = query.scalar() or 0
    return jsonify({'total_horas': float(total)})
