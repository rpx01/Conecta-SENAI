"""Rotas para controle de rateio de instrutores."""
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from src.models import db
from src.models.rateio_parametro import RateioParametro
from src.models.rateio_lancamento import RateioLancamento
from src.models.instrutor import Instrutor
from src.routes.user import verificar_autenticacao
from src.utils.error_handler import handle_internal_error
from src.schemas import (
    RateioParametroCreateSchema,
    RateioParametroUpdateSchema,
    RateioLancamentoCreateSchema,
    RateioLancamentoUpdateSchema,
)
from pydantic import ValidationError

rateio_bp = Blueprint('rateio', __name__)


def has_finance_permission(user):
    return user is not None and user.tipo in ['admin', 'financeiro']


@rateio_bp.route('/rateio/parametros', methods=['GET'])
def listar_parametros():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not has_finance_permission(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    params = RateioParametro.query.order_by(RateioParametro.id).all()
    return jsonify([p.to_dict() for p in params])


@rateio_bp.route('/rateio/parametros', methods=['POST'])
def criar_parametro():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not has_finance_permission(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    data = request.json or {}
    try:
        payload = RateioParametroCreateSchema(**data)
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400
    try:
        param = RateioParametro(
            filial=payload.filial,
            uo=payload.uo,
            cr=payload.cr,
            classe_valor=payload.classe_valor,
        )
        db.session.add(param)
        db.session.commit()
        return jsonify(param.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@rateio_bp.route('/rateio/parametros/<int:id>', methods=['PUT'])
def atualizar_parametro(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not has_finance_permission(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    param = db.session.get(RateioParametro, id)
    if not param:
        return jsonify({'erro': 'Parâmetro não encontrado'}), 404
    data = request.json or {}
    try:
        payload = RateioParametroUpdateSchema(**data)
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400
    if payload.filial is not None:
        param.filial = payload.filial
    if payload.uo is not None:
        param.uo = payload.uo
    if payload.cr is not None:
        param.cr = payload.cr
    if payload.classe_valor is not None:
        param.classe_valor = payload.classe_valor
    try:
        db.session.commit()
        return jsonify(param.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@rateio_bp.route('/rateio/parametros/<int:id>', methods=['DELETE'])
def remover_parametro(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not has_finance_permission(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    param = db.session.get(RateioParametro, id)
    if not param:
        return jsonify({'erro': 'Parâmetro não encontrado'}), 404
    try:
        db.session.delete(param)
        db.session.commit()
        return jsonify({'mensagem': 'Parâmetro removido'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@rateio_bp.route('/rateio/lancamentos', methods=['GET'])
def listar_lancamentos():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not has_finance_permission(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    instrutor_id = request.args.get('instrutor_id', type=int)
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)
    query = RateioLancamento.query
    if instrutor_id:
        query = query.filter(RateioLancamento.instrutor_id == instrutor_id)
    if mes:
        query = query.filter(RateioLancamento.mes == mes)
    if ano:
        query = query.filter(RateioLancamento.ano == ano)
    lancamentos = query.order_by(RateioLancamento.data_referencia).all()
    return jsonify([l.to_dict() for l in lancamentos])


@rateio_bp.route('/rateio/lancamentos', methods=['POST'])
def criar_lancamento():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not has_finance_permission(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    data = request.json or {}
    try:
        payload = RateioLancamentoCreateSchema(**data)
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400
    existe = RateioLancamento.query.filter_by(
        instrutor_id=payload.instrutor_id,
        mes=datetime.strptime(payload.data_referencia, '%Y-%m-%d').month,
        ano=datetime.strptime(payload.data_referencia, '%Y-%m-%d').year,
    ).first()
    if existe:
        return jsonify({'erro': 'Lançamento já existe para este instrutor e mês'}), 400
    try:
        lanc = RateioLancamento(
            instrutor_id=payload.instrutor_id,
            parametro_id=payload.parametro_id,
            data_referencia=payload.data_referencia,
            valor_total=payload.valor_total,
            horas_trabalhadas=payload.horas_trabalhadas,
            observacoes=payload.observacoes,
        )
        db.session.add(lanc)
        db.session.commit()
        return jsonify(lanc.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@rateio_bp.route('/rateio/lancamentos/<int:id>', methods=['PUT'])
def atualizar_lancamento(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not has_finance_permission(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    lanc = db.session.get(RateioLancamento, id)
    if not lanc:
        return jsonify({'erro': 'Lançamento não encontrado'}), 404
    data = request.json or {}
    try:
        payload = RateioLancamentoUpdateSchema(**data)
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400
    if payload.parametro_id is not None:
        lanc.parametro_id = payload.parametro_id
    if payload.data_referencia is not None:
        data_ref = datetime.strptime(payload.data_referencia, '%Y-%m-%d').date()
        lanc.data_referencia = data_ref
        lanc.mes = data_ref.month
        lanc.ano = data_ref.year
    if payload.valor_total is not None:
        lanc.valor_total = payload.valor_total
    if payload.horas_trabalhadas is not None:
        lanc.horas_trabalhadas = payload.horas_trabalhadas
    if payload.observacoes is not None:
        lanc.observacoes = payload.observacoes
    try:
        db.session.commit()
        return jsonify(lanc.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@rateio_bp.route('/rateio/lancamentos/<int:id>', methods=['DELETE'])
def remover_lancamento(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not has_finance_permission(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    lanc = db.session.get(RateioLancamento, id)
    if not lanc:
        return jsonify({'erro': 'Lançamento não encontrado'}), 404
    try:
        db.session.delete(lanc)
        db.session.commit()
        return jsonify({'mensagem': 'Lançamento removido'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)
