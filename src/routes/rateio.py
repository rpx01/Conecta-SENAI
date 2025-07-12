"""Rota para relatório financeiro de rateio."""
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from src.models import db
from src.models.apontamento import Apontamento
from src.routes.user import verificar_autenticacao, verificar_admin

rateio_bp = Blueprint('rateio', __name__)

@rateio_bp.route('/rateio/relatorio', methods=['GET'])
def relatorio_rateio():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    inicio = request.args.get('inicio')
    fim = request.args.get('fim')

    query = db.session.query(
        Apontamento.instrutor_id,
        Apontamento.centro_custo_id,
        func.sum(Apontamento.horas * (Apontamento.instrutor.custo_hora)).label('custo')
    ).join(Apontamento.instrutor)

    if inicio:
        query = query.filter(Apontamento.data >= inicio)
    if fim:
        query = query.filter(Apontamento.data <= fim)

    query = query.group_by(Apontamento.instrutor_id, Apontamento.centro_custo_id)

    resultados = [
        {
            'instrutor_id': r.instrutor_id,
            'centro_custo_id': r.centro_custo_id,
            'custo': float(r.custo or 0)
        }
        for r in query.all()
    ]
    return jsonify({'resultados': resultados})
