import pytest

from src.models import db
from src.models.ticket import Ticket, TicketComment
from src.models.user import User
from src.services import chamados_service


@pytest.fixture
def usuario_padrao(app):
    with app.app_context():
        usuario = db.session.get(User, 1)
        assert usuario is not None
        return usuario


def test_criacao_ticket_default(app, usuario_padrao):
    with app.app_context():
        dados = {
            'titulo': 'Computador não liga',
            'descricao': 'Ao pressionar o botão, nada acontece.',
            'categoria_id': 1,
            'prioridade_id': 2,
        }
        ticket = chamados_service.create_ticket(usuario_padrao.id, dados, [])
        assert ticket.status.nome == 'aberto'
        assert ticket.prioridade.nome == 'media'
        assert ticket.solicitante_id == usuario_padrao.id
        assert ticket.comentarios == []


def test_relacionamento_comentario(app, usuario_padrao):
    with app.app_context():
        dados = {
            'titulo': 'Monitor piscando',
            'descricao': 'Imagem falhando constantemente.',
            'categoria_id': 1,
            'prioridade_id': 2,
        }
        ticket = chamados_service.create_ticket(usuario_padrao.id, dados, [])
        comentario = chamados_service.add_comment(usuario_padrao.id, ticket.id, 'Já realizei o teste de cabos.')
        assert comentario.ticket_id == ticket.id
        assert isinstance(comentario, TicketComment)
        ticket_db = db.session.get(Ticket, ticket.id)
        assert len(ticket_db.comentarios) == 1
