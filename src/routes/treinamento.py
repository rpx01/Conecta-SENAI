"""Rotas para Agenda de Treinamentos."""
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from src.utils.error_handler import handle_internal_error
from src.routes.user import verificar_autenticacao, verificar_admin
from src.models import db, Treinamento, TurmaTreinamento, Inscricao, Presenca


treinamento_bp = Blueprint('treinamento', __name__)

# --- Treinamentos ---------------------------------------------------------
@treinamento_bp.route('/treinamentos', methods=['GET'])
def listar_treinamentos():
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    treins = Treinamento.query.all()
    return jsonify([t.to_dict() for t in treins])


@treinamento_bp.route('/treinamentos', methods=['POST'])
def criar_treinamento():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    data = request.json or {}
    nome = (data.get('nome') or '').strip()
    codigo = (data.get('codigo') or '').strip()
    if not nome or not codigo:
        return jsonify({'erro': 'Dados inválidos'}), 400
    try:
        novo = Treinamento(
            nome=nome,
            codigo=codigo,
            carga_horaria=data.get('carga_horaria'),
            status=data.get('status', 'ativo'),
            descricao=data.get('descricao'),
        )
        db.session.add(novo)
        db.session.commit()
        return jsonify(novo.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/treinamentos/<int:treinamento_id>', methods=['PUT'])
def atualizar_treinamento(treinamento_id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    treinamento = db.session.get(Treinamento, treinamento_id)
    if not treinamento:
        return jsonify({'erro': 'Treinamento não encontrado'}), 404

    data = request.json or {}
    treinamento.nome = data.get('nome', treinamento.nome)
    treinamento.codigo = data.get('codigo', treinamento.codigo)
    treinamento.carga_horaria = data.get('carga_horaria', treinamento.carga_horaria)
    treinamento.status = data.get('status', treinamento.status)
    treinamento.descricao = data.get('descricao', treinamento.descricao)
    try:
        db.session.commit()
        return jsonify(treinamento.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/treinamentos/<int:treinamento_id>', methods=['DELETE'])
def excluir_treinamento(treinamento_id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    treinamento = db.session.get(Treinamento, treinamento_id)
    if not treinamento:
        return jsonify({'erro': 'Treinamento não encontrado'}), 404
    try:
        db.session.delete(treinamento)
        db.session.commit()
        return jsonify({'mensagem': 'Excluído'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

# --- Turmas ---------------------------------------------------------------
@treinamento_bp.route('/turmas', methods=['GET'])
def listar_turmas():
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    turmas = TurmaTreinamento.query.all()
    return jsonify([t.to_dict() for t in turmas])


@treinamento_bp.route('/turmas', methods=['POST'])
def criar_turma():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    data = request.json or {}
    treinamento_id = data.get('treinamento_id')
    if not treinamento_id:
        return jsonify({'erro': 'Treinamento obrigatório'}), 400
    turma = TurmaTreinamento(
        treinamento_id=treinamento_id,
        nome=data.get('nome'),
        data_inicio=data.get('data_inicio'),
        data_fim=data.get('data_fim'),
        status=data.get('status', 'aberta'),
        vagas=data.get('vagas'),
    )
    try:
        db.session.add(turma)
        db.session.commit()
        return jsonify(turma.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/turmas/<int:turma_id>', methods=['PUT'])
def atualizar_turma(turma_id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    turma = db.session.get(TurmaTreinamento, turma_id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404

    data = request.json or {}
    turma.nome = data.get('nome', turma.nome)
    turma.data_inicio = data.get('data_inicio', turma.data_inicio)
    turma.data_fim = data.get('data_fim', turma.data_fim)
    turma.status = data.get('status', turma.status)
    turma.vagas = data.get('vagas', turma.vagas)
    try:
        db.session.commit()
        return jsonify(turma.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/turmas/<int:turma_id>', methods=['DELETE'])
def excluir_turma(turma_id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    turma = db.session.get(TurmaTreinamento, turma_id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404
    try:
        db.session.delete(turma)
        db.session.commit()
        return jsonify({'mensagem': 'Excluído'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

# --- Inscrições -----------------------------------------------------------
@treinamento_bp.route('/turmas/<int:turma_id>/inscricoes', methods=['POST'])
def inscrever(turma_id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    turma = db.session.get(TurmaTreinamento, turma_id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404

    inscricao = Inscricao(turma_id=turma_id, usuario_id=user.id)
    try:
        db.session.add(inscricao)
        db.session.commit()
        return jsonify(inscricao.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/inscricoes/<int:inscricao_id>/presencas', methods=['POST'])
def registrar_presenca(inscricao_id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    inscricao = db.session.get(Inscricao, inscricao_id)
    if not inscricao:
        return jsonify({'erro': 'Inscrição não encontrada'}), 404
    data = request.json or {}
    presenca = Presenca(
        inscricao_id=inscricao_id,
        data=data.get('data'),
        presente=data.get('presente', True),
    )
    try:
        db.session.add(presenca)
        db.session.commit()
        return jsonify(presenca.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)
