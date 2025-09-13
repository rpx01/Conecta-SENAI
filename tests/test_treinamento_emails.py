import jwt
from datetime import datetime, timedelta, date
from unittest.mock import patch

from src.models import db
from src.models.instrutor import Instrutor
from src.models.secretaria_treinamentos import SecretariaTreinamentos
from src.models.treinamento import Treinamento, TurmaTreinamento
from src.services.email_service import notificar_atualizacao_turma


def admin_headers(app):
    with app.app_context():
        from src.models.user import User
        user = User.query.filter_by(email='admin@example.com').first()
        token = jwt.encode({
            'user_id': user.id,
            'nome': user.nome,
            'perfil': user.tipo,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return {'Authorization': f'Bearer {token}'}


def test_notificar_nova_turma_enviada(client, app):
    headers = admin_headers(app)
    resp = client.post(
        '/api/treinamentos/catalogo',
        json={'nome': 'T', 'codigo': 'C1'},
        headers=headers,
    )
    treino_id = resp.get_json()['id']
    with app.app_context():
        inst = Instrutor(nome='Inst', email='inst@example.com')
        sec = SecretariaTreinamentos(nome='Sec', email='sec@example.com')
        db.session.add_all([inst, sec])
        db.session.commit()
        inst_id = inst.id
    hoje = date.today()
    payload = {
        'treinamento_id': treino_id,
        'data_inicio': hoje.isoformat(),
        'data_fim': (hoje + timedelta(days=1)).isoformat(),
        'instrutor_id': inst_id,
    }
    with patch('src.services.email_service.send_email') as mock_send:
        r = client.post(
            '/api/treinamentos/turmas',
            json=payload,
            headers=headers,
        )
        assert r.status_code == 201  # nosec B101
        destinatarios = {c.args[0] for c in mock_send.call_args_list}
        assert 'inst@example.com' in destinatarios  # nosec B101
        assert 'sec@example.com' in destinatarios  # nosec B101


def test_atualizar_turma_genera_diff(client, app):
    headers = admin_headers(app)
    r = client.post(
        '/api/treinamentos/catalogo',
        json={'nome': 'T2', 'codigo': 'C2'},
        headers=headers,
    )
    treino_id = r.get_json()['id']
    with app.app_context():
        inst = Instrutor(nome='I', email='i@example.com')
        db.session.add(inst)
        db.session.commit()
        inst_id = inst.id
    hoje = date.today()
    resp = client.post(
        '/api/treinamentos/turmas',
        json={
            'treinamento_id': treino_id,
            'data_inicio': hoje.isoformat(),
            'data_fim': (hoje + timedelta(days=1)).isoformat(),
            'local_realizacao': 'A',
            'instrutor_id': inst_id,
        },
        headers=headers,
    )
    turma_id = resp.get_json()['id']
    novo_inicio = hoje + timedelta(days=1)
    with patch(
        'src.routes.treinamentos.treinamento.notificar_atualizacao_turma'
    ) as mock_notify:
        resp_up = client.put(
            f'/api/treinamentos/turmas/{turma_id}',
            json={
                'data_inicio': novo_inicio.isoformat(),
                'local_realizacao': 'B',
            },
            headers=headers,
        )
        assert resp_up.status_code == 200  # nosec B101
        assert mock_notify.called  # nosec B101
        diff = mock_notify.call_args[0][1]
        assert diff['data_inicio'] == (
            hoje.strftime('%d/%m/%Y'),
            novo_inicio.strftime('%d/%m/%Y'),
        )  # nosec B101
        assert diff['local_realizacao'] == ('A', 'B')  # nosec B101


def test_notificar_atualizacao_envia_emails_instrutores(app):
    with app.app_context():
        treino = Treinamento(nome='T3', codigo='C3')
        inst_old = Instrutor(nome='Old', email='old@example.com')
        inst_new = Instrutor(nome='New', email='new@example.com')
        turma = TurmaTreinamento(
            treinamento=treino,
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=1),
            instrutor=inst_new,
        )
        sec = SecretariaTreinamentos(nome='Sec2', email='sec2@example.com')
        db.session.add_all([treino, inst_old, inst_new, turma, sec])
        db.session.commit()
        diff = {'instrutor': (inst_old.nome, inst_new.nome)}
        with patch('src.services.email_service.send_email') as mock_send:
            notificar_atualizacao_turma(turma, diff, inst_old)
            destinatarios = {c.args[0] for c in mock_send.call_args_list}
            assert destinatarios == {
                'sec2@example.com',
                'old@example.com',
                'new@example.com',
            }  # nosec B101


def test_notificar_atualizacao_instrutor_id(app):
    """Garante notificação ao instrutor antigo
    mesmo quando passado apenas o ID."""
    with app.app_context():
        treino = Treinamento(nome='T4', codigo='C4')
        inst_old = Instrutor(nome='Old2', email='old2@example.com')
        inst_new = Instrutor(nome='New2', email='new2@example.com')
        turma = TurmaTreinamento(
            treinamento=treino,
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=1),
            instrutor=inst_new,
        )
        sec = SecretariaTreinamentos(nome='Sec3', email='sec3@example.com')
        db.session.add_all([treino, inst_old, inst_new, turma, sec])
        db.session.commit()
        diff = {'instrutor': (inst_old.nome, inst_new.nome)}
        with patch('src.services.email_service.send_email') as mock_send:
            notificar_atualizacao_turma(turma, diff, inst_old.id)
            destinatarios = {c.args[0] for c in mock_send.call_args_list}
            assert destinatarios == {
                'sec3@example.com',
                'old2@example.com',
                'new2@example.com',
            }  # nosec B101
