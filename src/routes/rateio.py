"""Rotas para cálculo de rateio de instrutores."""
from flask import Blueprint, request, jsonify
from sqlalchemy import extract
from src.models import db
from src.models.apontamento import Apontamento
from src.models.instrutor import Instrutor
from src.models.centro_custo import CentroCusto
from src.routes.user import verificar_autenticacao, verificar_admin

rateio_bp = Blueprint('rateio', __name__)

@rateio_bp.route('/rateio/relatorio', methods=['GET'])
def relatorio_rateio():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado or not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)
    if not mes or not ano:
        return jsonify({'erro': 'Informe mes e ano'}), 400
    aps = (
        Apontamento.query
        .filter(extract('month', Apontamento.data) == mes)
        .filter(extract('year', Apontamento.data) == ano)
        .all()
    )
    resultado = {}
    for a in aps:
        cc = resultado.setdefault(a.centro_custo_id, {'total_horas': 0, 'total_custo': 0, 'instrutores': {}})
        cc['total_horas'] += float(a.horas)
        custo = float(a.horas) * float(a.instrutor.custo_hora)
        cc['total_custo'] += custo
        inst = cc['instrutores'].setdefault(a.instrutor_id, {'total_horas': 0, 'total_custo': 0})
        inst['total_horas'] += float(a.horas)
        inst['total_custo'] += custo
    saida = []
    for cc_id, dados in resultado.items():
        instrutores = [
            {
                'instrutor_id': iid,
                'total_horas': info['total_horas'],
                'total_custo': info['total_custo'],
            }
            for iid, info in dados['instrutores'].items()
        ]
        saida.append({
            'centro_custo_id': cc_id,
            'total_horas': dados['total_horas'],
            'total_custo': dados['total_custo'],
            'instrutores': instrutores,
        })
    return jsonify(saida)
