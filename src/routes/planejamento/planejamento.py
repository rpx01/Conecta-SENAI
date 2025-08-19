# flake8: noqa
"""Rotas para gerenciamento de itens do planejamento trimestral."""
from datetime import datetime
import hmac
from uuid import uuid4
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from src.models import db
from src.models.planejamento import PlanejamentoItem
from src.models.treinamento import Treinamento
from src.models.instrutor import Instrutor
from src.routes.user import verificar_autenticacao
from src.utils.error_handler import handle_internal_error
from pydantic import ValidationError
from src.schemas.planejamento import PlanejamentoCreateSchema

planejamento_bp = Blueprint('planejamento', __name__)


@planejamento_bp.before_request
def verificar_csrf():
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        token_cookie = request.cookies.get("csrf_token")
        token_header = request.headers.get("X-CSRF-Token") or request.headers.get("X-CSRFToken")
        if not token_cookie or not token_header or not hmac.compare_digest(token_cookie, token_header):
            return jsonify({"erro": "CSRF token inválido"}), 403


def _tabela_planejamento_existe() -> bool:
    """Verifica se a tabela de planejamento está presente no banco."""
    insp = inspect(db.engine)
    return insp.has_table(PlanejamentoItem.__tablename__)


@planejamento_bp.route('/planejamento', methods=['GET'])
def listar_planejamentos():
    """Lista todos os itens de planejamento."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    try:
        if not _tabela_planejamento_existe():
            return jsonify([]), 200
        itens = PlanejamentoItem.query.all()
        return jsonify([item.to_dict() for item in itens])
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@planejamento_bp.route('/planejamento/itens', methods=['GET'])
def listar_planejamento_itens():
    """Alias para listar itens de planejamento."""
    return listar_planejamentos()


@planejamento_bp.route('/planejamento', methods=['POST'])
def criar_planejamento():
    """Cria um ou mais itens de planejamento."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not _tabela_planejamento_existe():
        return (
            jsonify({'erro': 'Tabela planejamento_itens não existe; execute as migrações.'}),
            500,
        )

    payload = request.get_json() or {}
    try:
        dados = PlanejamentoCreateSchema(**payload)
    except ValidationError as exc:
        detalhes = {err['loc'][-1]: err['msg'] for err in exc.errors()}
        return jsonify({'erro': 'Dados inválidos', 'detalhes': detalhes}), 422

    lote_id = str(uuid4())
    itens = []
    detalhes = {}

    for registro in dados.registros:
        if not Treinamento.query.filter_by(nome=registro.treinamento).first():
            detalhes.setdefault('treinamento', 'Treinamento não encontrado')
        if not Instrutor.query.filter_by(nome=registro.instrutor).first():
            detalhes.setdefault('instrutor', 'Instrutor não encontrado')

    if detalhes:
        return jsonify({'erro': 'Dados inválidos', 'detalhes': detalhes}), 422

    for registro in dados.registros:
        item = PlanejamentoItem(
            row_id=str(uuid4()),
            lote_id=lote_id,
            data=registro.inicio,
            semana=registro.semana,
            horario=registro.horario,
            carga_horaria=str(registro.carga_horaria),
            modalidade=registro.modalidade,
            treinamento=registro.treinamento,
            cmd=str(registro.polos.cmd),
            sjb=str(registro.polos.sjb),
            sag_tombos=str(registro.polos.sag_tombos),
            instrutor=registro.instrutor,
            local=registro.local,
            observacao=registro.observacao,
        )
        itens.append(item)

    try:
        for item in itens:
            db.session.add(item)
        db.session.commit()
        return jsonify({'mensagem': 'Planejamento salvo', 'quantidade': len(itens)}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.exception('Erro ao criar planejamento', extra={'payload': payload})
        return handle_internal_error(e)


@planejamento_bp.route('/planejamento/itens', methods=['POST'])
def criar_planejamento_item():
    """Cria um único item de planejamento."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not _tabela_planejamento_existe():
        return (
            jsonify({'erro': 'Tabela planejamento_itens não existe; execute as migrações.'}),
            500,
        )

    data = request.get_json() or {}
    data_str = data.get('data')
    horario = data.get('horario')
    treinamento = data.get('treinamento')
    instrutor_nome = data.get('instrutor')

    if not data_str or not horario or not treinamento:
        return jsonify({'erro': 'Dados obrigatórios ausentes'}), 422

    try:
        data_obj = datetime.fromisoformat(data_str).date()
    except Exception:
        return jsonify({'erro': 'Data inválida'}), 400

    detalhes = {}
    if not Treinamento.query.filter_by(nome=treinamento).first():
        detalhes.setdefault('treinamento', 'Treinamento não encontrado')
    if not Instrutor.query.filter_by(nome=instrutor_nome).first():
        detalhes.setdefault('instrutor', 'Instrutor não encontrado')
    if detalhes:
        return jsonify({'erro': 'Dados inválidos', 'detalhes': detalhes}), 422

    item = PlanejamentoItem(
        row_id=str(uuid4()),
        lote_id=data.get('loteId') or str(uuid4()),
        data=data_obj,
        semana=data.get('semana'),
        horario=horario,
        carga_horaria=str(data.get('carga_horaria') or data.get('cargaHoraria') or ''),
        modalidade=data.get('modalidade'),
        treinamento=treinamento,
        cmd=str(data.get('cmd')),
        sjb=str(data.get('sjb')),
        sag_tombos=str(data.get('sag_tombos') or data.get('sagTombos')),
        instrutor=instrutor_nome,
        local=data.get('local'),
        observacao=data.get('observacao'),
    )
    try:
        db.session.add(item)
        db.session.commit()
        return jsonify(item.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@planejamento_bp.route('/planejamento/itens/<int:item_id>', methods=['PUT'])
def atualizar_planejamento_item(item_id):
    """Atualiza um item de planejamento pelo ID."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not _tabela_planejamento_existe():
        return (
            jsonify({'erro': 'Tabela planejamento_itens não existe; execute as migrações.'}),
            500,
        )

    item = PlanejamentoItem.query.get(item_id)
    if not item:
        return jsonify({'erro': 'Item não encontrado'}), 404

    data = request.get_json() or {}
    data_str = data.get('data')
    try:
        data_obj = datetime.fromisoformat(data_str).date()
    except Exception:
        return jsonify({'erro': 'Data inválida'}), 400

    item.data = data_obj
    item.semana = data.get('semana')
    item.horario = data.get('horario')
    item.carga_horaria = data.get('carga_horaria') or data.get('cargaHoraria')
    item.modalidade = data.get('modalidade')
    item.treinamento = data.get('treinamento')
    item.cmd = data.get('cmd')
    item.sjb = data.get('sjb')
    item.sag_tombos = data.get('sag_tombos') or data.get('sagTombos')
    item.instrutor = data.get('instrutor')
    item.local = data.get('local')
    item.observacao = data.get('observacao')
    item.lote_id = data.get('loteId', item.lote_id)

    try:
        db.session.commit()
        return jsonify(item.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@planejamento_bp.route('/planejamento/itens/<int:item_id>', methods=['DELETE'])
def excluir_planejamento_item(item_id):
    """Remove um item de planejamento pelo ID."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not _tabela_planejamento_existe():
        return (
            jsonify({'erro': 'Tabela planejamento_itens não existe; execute as migrações.'}),
            500,
        )

    item = PlanejamentoItem.query.get(item_id)
    if not item:
        return jsonify({'erro': 'Item não encontrado'}), 404

    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'mensagem': 'Item excluído com sucesso'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@planejamento_bp.route('/planejamento/<string:row_id>', methods=['PUT'])
def atualizar_planejamento(row_id):
    """Atualiza um item existente."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not _tabela_planejamento_existe():
        return (
            jsonify({'erro': 'Tabela planejamento_itens não existe; execute as migrações.'}),
            500,
        )

    item = PlanejamentoItem.query.filter_by(row_id=row_id).first()
    if not item:
        return jsonify({'erro': 'Item não encontrado'}), 404

    data = request.json or {}
    data_str = data.get('data')
    try:
        data_obj = datetime.fromisoformat(data_str).date()
    except Exception:
        return jsonify({'erro': 'Data inválida'}), 400

    item.data = data_obj
    item.semana = data.get('semana')
    item.horario = data.get('horario')
    item.carga_horaria = data.get('cargaHoraria')
    item.modalidade = data.get('modalidade')
    item.treinamento = data.get('treinamento')
    item.cmd = data.get('cmd')
    item.sjb = data.get('sjb')
    item.sag_tombos = data.get('sagTombos')
    item.instrutor = data.get('instrutor')
    item.local = data.get('local')
    item.observacao = data.get('observacao')

    try:
        db.session.commit()
        return jsonify(item.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@planejamento_bp.route(
    '/planejamento/lote/<string:lote_id>', methods=['DELETE']
)
def excluir_lote(lote_id):
    """Remove todos os itens pertencentes a um lote."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not _tabela_planejamento_existe():
        return (
            jsonify({'erro': 'Tabela planejamento_itens não existe; execute as migrações.'}),
            500,
        )

    try:
        PlanejamentoItem.query.filter_by(lote_id=lote_id).delete()
        db.session.commit()
        return jsonify({'mensagem': 'Lote excluído com sucesso'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@planejamento_bp.route('/planejamento/schema', methods=['GET'])
def schema_planejamento():
    """Retorna o schema esperado para o planejamento."""
    return jsonify(PlanejamentoCreateSchema.model_json_schema())
