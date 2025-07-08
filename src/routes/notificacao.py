"""Rotas para notificacoes de agendamentos."""
from flask import Blueprint, request, jsonify
from src.models import db
from src.models.agendamento import Notificacao
from src.routes.user import verificar_autenticacao, verificar_admin
from sqlalchemy.exc import SQLAlchemyError
from src.utils.error_handler import handle_internal_error

notificacao_bp = Blueprint('notificacao', __name__)

@notificacao_bp.route('/notificacoes', methods=['GET'])
def listar_notificacoes():
    """
    Lista notificações de agendamentos próximos.
    Usuários comuns veem apenas suas próprias notificações.
    Administradores podem ver todas as notificações.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    if verificar_admin(user):
        # Administradores podem ver todas as notificações
        notificacoes = Notificacao.query.order_by(Notificacao.data_criacao.desc()).all()
    else:
        # Usuários comuns veem apenas suas próprias notificações
        notificacoes = Notificacao.query.filter_by(usuario_id=user.id).order_by(Notificacao.data_criacao.desc()).all()
    
    return jsonify([n.to_dict() for n in notificacoes])

@notificacao_bp.route('/notificacoes/<int:id>/marcar-lida', methods=['PUT'])
def marcar_notificacao_lida(id):
    """
    Marca uma notificação como lida.
    Usuários só podem marcar suas próprias notificações como lidas.
    Administradores podem marcar qualquer notificação como lida.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    notificacao = db.session.get(Notificacao, id)
    if not notificacao:
        return jsonify({'erro': 'Notificação não encontrada'}), 404
    
    # Verifica permissões
    if not verificar_admin(user) and notificacao.usuario_id != user.id:
        return jsonify({'erro': 'Permissão negada'}), 403
    
    try:
        notificacao.marcar_como_lida()
        db.session.commit()
        return jsonify(notificacao.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

# Função para criar notificações de agendamentos próximos
def criar_notificacoes_agendamentos_proximos():
    """
    Cria notificações para agendamentos próximos.
    Esta função seria chamada por um job agendado.
    """
    from datetime import datetime, timedelta
    from src.models.agendamento import Agendamento
    
    # Define o período para notificação (ex: próximas 24 horas)
    agora = datetime.utcnow()
    limite = agora + timedelta(hours=24)
    
    # Busca agendamentos no período
    agendamentos_proximos = Agendamento.query.filter(
        Agendamento.data >= agora.date(),
        Agendamento.data <= limite.date()
    ).all()
    
    for agendamento in agendamentos_proximos:
        # Verifica se já existe notificação para este agendamento
        notificacao_existente = Notificacao.query.filter_by(
            agendamento_id=agendamento.id,
            lida=False
        ).first()
        
        if not notificacao_existente:
            # Cria uma nova notificação
            mensagem = f"Lembrete: Você tem um agendamento para {agendamento.laboratorio} em {agendamento.data.strftime('%d/%m/%Y')}."
            
            nova_notificacao = Notificacao(
                usuario_id=agendamento.usuario_id,
                agendamento_id=agendamento.id,
                mensagem=mensagem
            )
            
            db.session.add(nova_notificacao)
    
    try:
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        handle_internal_error(e)
        return False
