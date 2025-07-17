"""Rotas para gerenciamento de treinamentos e turmas."""
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError

from src.models import db, Treinamento, TurmaTreinamento, Inscricao, Presenca
from src.routes.user import verificar_autenticacao, verificar_admin
from src.utils.error_handler import handle_internal_error


treinamento_bp = Blueprint('treinamento', __name__)


# ---- Treinamentos ---------------------------------------------------------

@treinamento_bp.route('/treinamentos', methods=['GET'])
def listar_treinamentos():
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    treins = Treinamento.query.all()
    return jsonify([t.to_dict() for t in treins])


@treinamento_bp.route('/treinamentos/<int:id>', methods=['GET'])
def obter_treinamento(id):
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    treino = db.session.get(Treinamento, id)
    if not treino:
        return jsonify({'erro': 'Treinamento não encontrado'}), 404
    return jsonify(treino.to_dict())


@treinamento_bp.route('/treinamentos', methods=['POST'])
def criar_treinamento():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    data = request.json or {}
    try:
        novo = Treinamento(
            nome=data.get('nome'),
            codigo=data.get('codigo'),
            descricao=data.get('descricao'),
            carga_horaria=data.get('carga_horaria'),
            status=data.get('status', 'ativo'),
        )
        db.session.add(novo)
        db.session.commit()
        return jsonify(novo.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/treinamentos/<int:id>', methods=['PUT'])
def atualizar_treinamento(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    treino = db.session.get(Treinamento, id)
    if not treino:
        return jsonify({'erro': 'Treinamento não encontrado'}), 404
    data = request.json or {}
    treino.nome = data.get('nome', treino.nome)
    treino.codigo = data.get('codigo', treino.codigo)
    treino.descricao = data.get('descricao', treino.descricao)
    treino.carga_horaria = data.get('carga_horaria', treino.carga_horaria)
    treino.status = data.get('status', treino.status)
    try:
        db.session.commit()
        return jsonify(treino.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/treinamentos/<int:id>', methods=['DELETE'])
def remover_treinamento(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    treino = db.session.get(Treinamento, id)
    if not treino:
        return jsonify({'erro': 'Treinamento não encontrado'}), 404
    try:
        db.session.delete(treino)
        db.session.commit()
        return jsonify({'mensagem': 'Treinamento removido'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


# ---- Turmas ---------------------------------------------------------------

@treinamento_bp.route('/turmas', methods=['GET'])
def listar_turmas():
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    turmas = TurmaTreinamento.query.all()
    return jsonify([t.to_dict() for t in turmas])


@treinamento_bp.route('/turmas/<int:id>', methods=['GET'])
def obter_turma(id):
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    turma = db.session.get(TurmaTreinamento, id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404
    return jsonify(turma.to_dict())


@treinamento_bp.route('/turmas', methods=['POST'])
def criar_turma():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    data = request.json or {}
    try:
        nova = TurmaTreinamento(
            treinamento_id=data.get('treinamento_id'),
            nome=data.get('nome'),
            data_inicio=data.get('data_inicio'),
            data_fim=data.get('data_fim'),
            vagas=data.get('vagas'),
            status=data.get('status', 'aberta'),
        )
        db.session.add(nova)
        db.session.commit()
        return jsonify(nova.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/turmas/<int:id>', methods=['PUT'])
def atualizar_turma(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    turma = db.session.get(TurmaTreinamento, id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404
    data = request.json or {}
    turma.nome = data.get('nome', turma.nome)
    turma.data_inicio = data.get('data_inicio', turma.data_inicio)
    turma.data_fim = data.get('data_fim', turma.data_fim)
    turma.vagas = data.get('vagas', turma.vagas)
    turma.status = data.get('status', turma.status)
    try:
        db.session.commit()
        return jsonify(turma.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/turmas/<int:id>', methods=['DELETE'])
def remover_turma(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    turma = db.session.get(TurmaTreinamento, id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404
    try:
        db.session.delete(turma)
        db.session.commit()
        return jsonify({'mensagem': 'Turma removida'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


# ---- Inscricoes e Presencas ----------------------------------------------

@treinamento_bp.route('/inscricoes', methods=['POST'])
def inscrever_usuario():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    data = request.json or {}
    try:
        nova = Inscricao(
            turma_id=data.get('turma_id'),
            usuario_id=user.id,
        )
        db.session.add(nova)
        db.session.commit()
        return jsonify(nova.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/inscricoes/<int:id>/presencas', methods=['POST'])
def registrar_presenca(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    inscricao = db.session.get(Inscricao, id)
    if not inscricao:
        return jsonify({'erro': 'Inscrição não encontrada'}), 404
    if inscricao.usuario_id != user.id and not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    data = request.json or {}
    try:
        pres = Presenca(
            inscricao_id=id,
            data=data.get('data'),
            presente=data.get('presente', True),
        )
        db.session.add(pres)
        db.session.commit()
        return jsonify(pres.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

