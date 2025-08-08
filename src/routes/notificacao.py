"""Rotas para notificacoes de agendamentos."""
from flask import Blueprint, request, jsonify
from src.routes.user import verificar_autenticacao
from src.services.notificacao_service import (
    listar_notificacoes as listar_notificacoes_service,
    marcar_notificacao_lida as marcar_notificacao_lida_service,
)


notificacao_bp = Blueprint('notificacao', __name__)

@notificacao_bp.route('/notificacoes', methods=['GET'])
def listar_notificacoes():
    """Retorna notificações ordenadas por data de criação.

    A rota exige autenticação e aplica regras de visibilidade
    baseadas no perfil do usuário:

    * Usuários comuns recebem apenas notificações associadas ao
      seu próprio ``usuario_id``;
    * Administradores podem visualizar todas as notificações do
      sistema.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    return listar_notificacoes_service(user)

@notificacao_bp.route('/notificacoes/<int:id>/marcar-lida', methods=['PUT'])
def marcar_notificacao_lida(id):
    """Marca uma notificação como lida.

    Requer autenticação: usuários comuns só podem alterar notificações
    das quais são proprietários, enquanto administradores podem atuar
    sobre qualquer uma. Retorna ``404`` se a notificação não existir e
    ``403`` quando o usuário não possui permissão.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    return marcar_notificacao_lida_service(id, user)

