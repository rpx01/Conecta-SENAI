"""Rotas para gerenciamento de laboratorios."""
from flask import Blueprint, request, jsonify
from src.models import db
from src.models.laboratorio_turma import Laboratorio
from src.auth import login_required, admin_required
from sqlalchemy.exc import SQLAlchemyError
from src.utils.error_handler import handle_internal_error
from flasgger import swag_from

laboratorio_bp = Blueprint('laboratorio', __name__)

@laboratorio_bp.route('/laboratorios', methods=['GET'])
@swag_from({
    'tags': ['Laboratórios'],
    'responses': {200: {'description': 'Lista de laboratórios'}}
})
@login_required
def listar_laboratorios():
    """Lista todos os laboratórios disponíveis."""
    try:
        laboratorios = Laboratorio.query.all()
        return jsonify([lab.to_dict() for lab in laboratorios])
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@laboratorio_bp.route('/laboratorios/<int:id>', methods=['GET'])
@swag_from({
    'tags': ['Laboratórios'],
    'parameters': [
        {'in': 'path', 'name': 'id', 'schema': {'type': 'integer'}, 'required': True},
    ],
    'responses': {
        200: {'description': 'Detalhes do laboratório'},
        404: {'description': 'Laboratório não encontrado'},
    },
})
@login_required
def obter_laboratorio(id):
    """
    Obtém detalhes de um laboratório específico.
    Acessível para todos os usuários autenticados.
    """
    laboratorio = db.session.get(Laboratorio, id)
    if not laboratorio:
        return jsonify({'erro': 'Laboratório não encontrado'}), 404
    
    return jsonify(laboratorio.to_dict())

@laboratorio_bp.route('/laboratorios', methods=['POST'])
@swag_from({
    'tags': ['Laboratórios'],
    'requestBody': {
        'required': True,
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'nome': {'type': 'string'},
                        'classe_icone': {'type': 'string'},
                    },
                    'required': ['nome'],
                }
            }
        }
    },
    'responses': {
        201: {'description': 'Laboratório criado'},
        400: {'description': 'Dados inválidos'},
    },
})
@admin_required
def criar_laboratorio():
    """
    Cria um novo laboratório.
    Apenas administradores podem criar laboratórios.
    """
    data = request.json
    
    # Validação de dados
    if 'nome' not in data or not data['nome'].strip():
        return jsonify({'erro': 'Nome do laboratório é obrigatório'}), 400
    
    # Verifica se já existe um laboratório com o mesmo nome
    if Laboratorio.query.filter_by(nome=data['nome']).first():
        return jsonify({'erro': 'Já existe um laboratório com este nome'}), 400

    # Cria o laboratório
    try:
        novo_laboratorio = Laboratorio(
            nome=data['nome'],
            classe_icone=data.get('classe_icone')
        )
        db.session.add(novo_laboratorio)
        db.session.commit()
        return jsonify(novo_laboratorio.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@laboratorio_bp.route('/laboratorios/<int:id>', methods=['PUT'])
@swag_from({
    'tags': ['Laboratórios'],
    'parameters': [
        {'in': 'path', 'name': 'id', 'schema': {'type': 'integer'}, 'required': True},
    ],
    'requestBody': {
        'required': True,
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'nome': {'type': 'string'},
                        'classe_icone': {'type': 'string'},
                    },
                    'required': ['nome'],
                }
            }
        }
    },
    'responses': {
        200: {'description': 'Laboratório atualizado'},
        400: {'description': 'Dados inválidos'},
        404: {'description': 'Laboratório não encontrado'},
    },
})
@admin_required
def atualizar_laboratorio(id):
    """
    Atualiza um laboratório existente.
    Apenas administradores podem atualizar laboratórios.
    """
    laboratorio = db.session.get(Laboratorio, id)
    if not laboratorio:
        return jsonify({'erro': 'Laboratório não encontrado'}), 404
    
    data = request.json
    
    # Validação de dados
    if 'nome' not in data or not data['nome'].strip():
        return jsonify({'erro': 'Nome do laboratório é obrigatório'}), 400
    
    # Verifica se já existe outro laboratório com o mesmo nome
    lab_existente = Laboratorio.query.filter_by(nome=data['nome']).first()
    if lab_existente and lab_existente.id != id:
        return jsonify({'erro': 'Já existe outro laboratório com este nome'}), 400
    
    # Atualiza o laboratório
    try:
        laboratorio.nome = data['nome']
        laboratorio.classe_icone = data.get('classe_icone', laboratorio.classe_icone)
        db.session.commit()
        return jsonify(laboratorio.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@laboratorio_bp.route('/laboratorios/<int:id>', methods=['DELETE'])
@swag_from({
    'tags': ['Laboratórios'],
    'parameters': [
        {'in': 'path', 'name': 'id', 'schema': {'type': 'integer'}, 'required': True},
    ],
    'responses': {
        200: {'description': 'Laboratório removido'},
        404: {'description': 'Laboratório não encontrado'},
    },
})
@admin_required
def remover_laboratorio(id):
    """
    Remove um laboratório.
    Apenas administradores podem remover laboratórios.
    """
    laboratorio = db.session.get(Laboratorio, id)
    if not laboratorio:
        return jsonify({'erro': 'Laboratório não encontrado'}), 404
    
    try:
        db.session.delete(laboratorio)
        db.session.commit()
        return jsonify({'mensagem': 'Laboratório removido com sucesso'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)
