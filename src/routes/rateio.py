from flask import Blueprint, request, jsonify
from sqlalchemy import func

from src.models import db
from src.models.apontamento import Apontamento
from src.models.instrutor import Instrutor
from src.models.centro_custo import CentroCusto
from src.auth import login_required

rateio_bp = Blueprint('rateio', __name__)

@rateio_bp.route('/rateio/resumo', methods=['GET'])
@login_required
def resumo_rateio():
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    query = db.session.query(
        CentroCusto.nome.label('centro_custo'),
        func.sum(Apontamento.horas).label('total_horas'),
        func.sum(Apontamento.horas * Instrutor.custo_hora).label('custo_total')
    ).join(CentroCusto, Apontamento.centro_custo_id == CentroCusto.id
    ).join(Instrutor, Apontamento.instrutor_id == Instrutor.id)
    if data_inicio:
        query = query.filter(Apontamento.data >= data_inicio)
    if data_fim:
        query = query.filter(Apontamento.data <= data_fim)
    resultados = query.group_by(CentroCusto.nome).all()
    retorno = [
        {
            'centro_custo': r.centro_custo,
            'total_horas': float(r.total_horas or 0),
            'custo_total': float(r.custo_total or 0)
        }
        for r in resultados
    ]
    return jsonify(retorno)
