"""Rotas para gerenciamento de turmas."""
from flask import Blueprint, request, jsonify
from src.models import db
from sqlalchemy.exc import SQLAlchemyError
from src.utils.error_handler import handle_internal_error
from src.models.laboratorio_turma import Turma
from src.routes.user import verificar_autenticacao, verificar_admin

turma_bp = Blueprint('turma', __name__)

@turma_bp.route('/turmas', methods=['GET'])
def listar_turmas():
    """
    Lista todas as turmas disponíveis.
    Acessível para todos os usuários autenticados.
    """
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    turmas = Turma.query.all()
    return jsonify([turma.to_dict() for turma in turmas])

@turma_bp.route('/turmas/<int:id>', methods=['GET'])
def obter_turma(id):
    """
    Obtém detalhes de uma turma específica.
    Acessível para todos os usuários autenticados.
    """
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    turma = db.session.get(Turma, id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404
    
    return jsonify(turma.to_dict())

@turma_bp.route('/turmas', methods=['POST'])
def criar_turma():
    """
    Cria uma nova turma.
    Apenas administradores podem criar turmas.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    # Verifica permissões de administrador
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    
    data = request.json or {}

    nome = (data.get('nome') or '').strip()

    # Validação de dados
    if not nome:
        return jsonify({'erro': 'Nome da turma é obrigatório'}), 400

    # Verifica se já existe uma turma com o mesmo nome
    if Turma.query.filter_by(nome=nome).first():
        return jsonify({'erro': 'Já existe uma turma com este nome'}), 400

    # Cria a turma
    try:
        nova_turma = Turma(nome=nome)
        db.session.add(nova_turma)
        db.session.commit()
        return jsonify(nova_turma.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@turma_bp.route('/turmas/<int:id>', methods=['PUT'])
def atualizar_turma(id):
    """
    Atualiza uma turma existente.
    Apenas administradores podem atualizar turmas.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    # Verifica permissões de administrador
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    
    turma = db.session.get(Turma, id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404
    
    data = request.json or {}

    nome = (data.get('nome') or '').strip()

    # Validação de dados
    if not nome:
        return jsonify({'erro': 'Nome da turma é obrigatório'}), 400

    # Verifica se já existe outra turma com o mesmo nome
    turma_existente = Turma.query.filter_by(nome=nome).first()
    if turma_existente and turma_existente.id != id:
        return jsonify({'erro': 'Já existe outra turma com este nome'}), 400

    # Atualiza a turma
    try:
        turma.nome = nome
        db.session.commit()
        return jsonify(turma.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@turma_bp.route('/turmas/<int:id>', methods=['DELETE'])
def remover_turma(id):
    """
    Remove uma turma.
    Apenas administradores podem remover turmas.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    # Verifica permissões de administrador
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    
    turma = db.session.get(Turma, id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404
    
    try:
        db.session.delete(turma)
        db.session.commit()
        return jsonify({'mensagem': 'Turma removida com sucesso'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)
