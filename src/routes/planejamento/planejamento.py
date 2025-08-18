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
        if not Treinamento.query.get(registro.treinamento_id):
            detalhes.setdefault('treinamento_id', 'Treinamento não encontrado')
        if not Instrutor.query.get(registro.instrutor_id):
            detalhes.setdefault('instrutor_id', 'Instrutor não encontrado')

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
            treinamento=str(registro.treinamento_id),
            cmd=str(registro.polos.cmd),
            sjb=str(registro.polos.sjb),
            sag_tombos=str(registro.polos.sag_tombos),
            instrutor=str(registro.instrutor_id),
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
