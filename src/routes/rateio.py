from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from src.models import db
from src.models.rateio import RateioConfig, LancamentoRateio
from src.auth import admin_required
from src.utils.error_handler import handle_internal_error
from src.schemas import RateioConfigCreateSchema, LancamentoRateioSchema
from pydantic import ValidationError

rateio_bp = Blueprint('rateio', __name__)


@rateio_bp.route('/rateio-configs', methods=['GET'])
@admin_required
def listar_configs():
    configs = RateioConfig.query.order_by(RateioConfig.filial, RateioConfig.uo).all()
    return jsonify([c.to_dict() for c in configs])


@rateio_bp.route('/rateio-configs/<int:id>', methods=['GET'])
@admin_required
def obter_config(id):
    config = db.session.get(RateioConfig, id)
    if not config:
        return jsonify({'erro': 'Configuração não encontrada'}), 404
    return jsonify(config.to_dict())


@rateio_bp.route('/rateio-configs', methods=['POST'])
@admin_required
def criar_config():
    data = request.json or {}
    try:
        payload = RateioConfigCreateSchema(**data)
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400

    try:
        nova_config = RateioConfig(**payload.model_dump())
        db.session.add(nova_config)
        db.session.commit()
        return jsonify(nova_config.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'erro': 'Esta configuração de rateio já existe.'}), 409
    except Exception as e:  # pragma: no cover - proteção extra
        db.session.rollback()
        return handle_internal_error(e)


@rateio_bp.route('/rateio-configs/<int:id>', methods=['PUT'])
@admin_required
def atualizar_config(id):
    config = db.session.get(RateioConfig, id)
    if not config:
        return jsonify({'erro': 'Configuração não encontrada'}), 404

    data = request.json or {}
    try:
        config.filial = data.get('filial', config.filial)
        config.uo = data.get('uo', config.uo)
        config.cr = data.get('cr', config.cr)
        config.classe_valor = data.get('classe_valor', config.classe_valor)
        config.descricao = data.get('descricao', config.descricao)
        db.session.commit()
        return jsonify(config.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({'erro': 'Já existe outra configuração com estes dados.'}), 409
    except Exception as e:
        db.session.rollback()
        return handle_internal_error(e)


@rateio_bp.route('/rateio-configs/<int:id>', methods=['DELETE'])
@admin_required
def deletar_config(id):
    config = db.session.get(RateioConfig, id)
    if not config:
        return jsonify({'erro': 'Configuração não encontrada'}), 404

    if LancamentoRateio.query.filter_by(rateio_config_id=id).first():
        return jsonify({'erro': 'Configuração em uso, não pode ser excluída.'}), 400

    db.session.delete(config)
    db.session.commit()
    return jsonify({'mensagem': 'Configuração excluída com sucesso'})


@rateio_bp.route('/rateio/lancamentos', methods=['GET'])
@admin_required
def get_lancamentos():
    instrutor_id = request.args.get('instrutor_id', type=int)
    ano = request.args.get('ano', type=int)
    mes = request.args.get('mes', type=int)

    if not all([instrutor_id, ano, mes]):
        return jsonify({'erro': 'Parâmetros instrutor_id, ano e mes são obrigatórios'}), 400

    lancamentos = LancamentoRateio.query.filter_by(
        instrutor_id=instrutor_id, ano=ano, mes=mes
    ).all()

    return jsonify([l.to_dict() for l in lancamentos])


@rateio_bp.route('/rateio/lancamentos-ano', methods=['GET'])
@admin_required
def get_lancamentos_ano():
    """Retorna todos os lancamentos de um instrutor em um determinado ano."""
    instrutor_id = request.args.get('instrutor_id', type=int)
    ano = request.args.get('ano', type=int)

    if not instrutor_id or not ano:
        return jsonify({'erro': 'Parâmetros instrutor_id e ano são obrigatórios'}), 400

    lancamentos = LancamentoRateio.query.filter_by(instrutor_id=instrutor_id, ano=ano).all()

    agrupados = {}
    for l in lancamentos:
        agrupados.setdefault(l.mes, []).append(l.to_dict())

    # Garante um dicionário com todas as chaves de 1 a 12
    resultado = {mes: agrupados.get(mes, []) for mes in range(1, 13)}
    return jsonify(resultado)


@rateio_bp.route('/rateio/lancamentos', methods=['POST'])
@admin_required
def salvar_lancamentos():
    data = request.json or {}
    try:
        payload = LancamentoRateioSchema(**data)
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400

    total_percentual = sum(item.percentual for item in payload.lancamentos)
    if total_percentual > 100:
        return jsonify({'erro': f'O percentual total ({total_percentual}%) não pode exceder 100%.'}), 400

    try:
        LancamentoRateio.query.filter_by(instrutor_id=payload.instrutor_id, ano=payload.ano, mes=payload.mes).delete()

        novos = []
        for item in payload.lancamentos:
            if item.percentual > 0:
                novo = LancamentoRateio(
                    instrutor_id=payload.instrutor_id,
                    ano=payload.ano,
                    mes=payload.mes,
                    rateio_config_id=item.rateio_config_id,
                    percentual=item.percentual,
                )
                novos.append(novo)
        db.session.add_all(novos)
        db.session.commit()
        return jsonify({'mensagem': 'Lançamentos salvos com sucesso!'}), 201
    except Exception as e:  # pragma: no cover - segurança
        db.session.rollback()
        return handle_internal_error(e)
