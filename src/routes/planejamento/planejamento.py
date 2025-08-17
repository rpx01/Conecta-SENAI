"""Rotas para gerenciamento de itens do planejamento trimestral."""
from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from src.models import db
from src.models.planejamento import PlanejamentoItem
from src.routes.user import verificar_autenticacao
from src.utils.error_handler import handle_internal_error

planejamento_bp = Blueprint('planejamento', __name__)


@planejamento_bp.route('/planejamento', methods=['GET'])
def listar_planejamentos():
    """Lista todos os itens de planejamento."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    try:
        itens = PlanejamentoItem.query.all()
        return jsonify([item.to_dict() for item in itens])
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@planejamento_bp.route('/planejamento', methods=['POST'])
def criar_planejamento():
    """Cria um novo item de planejamento."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    data = request.json or {}
    data_str = data.get('data')
    try:
        data_obj = datetime.fromisoformat(data_str).date()
    except Exception:
        return jsonify({'erro': 'Data inválida'}), 400

    item = PlanejamentoItem(
        row_id=data.get('rowId'),
        lote_id=data.get('loteId'),
        data=data_obj,
        semana=data.get('semana'),
        horario=data.get('horario'),
        carga_horaria=data.get('cargaHoraria'),
        modalidade=data.get('modalidade'),
        treinamento=data.get('treinamento'),
        cmd=data.get('cmd'),
        sjb=data.get('sjb'),
        sag_tombos=data.get('sagTombos'),
        instrutor=data.get('instrutor'),
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


@planejamento_bp.route('/planejamento/<string:row_id>', methods=['PUT'])
def atualizar_planejamento(row_id):
    """Atualiza um item existente."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

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

    try:
        PlanejamentoItem.query.filter_by(lote_id=lote_id).delete()
        db.session.commit()
        return jsonify({'mensagem': 'Lote excluído com sucesso'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)
