from datetime import date, datetime, timedelta
import jwt

from src.models import (
    db,
    Treinamento,
    TurmaTreinamento,
    InscricaoTreinamento,
)


def admin_headers(app):
    with app.app_context():
        from src.models.user import User
        user = User.query.filter_by(email='admin@example.com').first()
        token = jwt.encode(
            {
                'user_id': user.id,
                'nome': user.nome,
                'perfil': user.tipo,
                'exp': datetime.utcnow() + timedelta(hours=1),
            },
            app.config['SECRET_KEY'],
            algorithm='HS256',
        )
        return {'Authorization': f'Bearer {token}'}


def test_convocar_inscrito(client, app, monkeypatch):
    headers = admin_headers(app)
    with app.app_context():
        treino = Treinamento(
            nome='Treino', codigo='T1', carga_horaria=8, tem_pratica=True
        )
        db.session.add(treino)
        db.session.commit()
        turma = TurmaTreinamento(
            treinamento_id=treino.id,
            data_inicio=date.today(),
            data_fim=date.today(),
            local_realizacao='Local',
            horario='08h',
            teoria_online=True,
        )
        db.session.add(turma)
        db.session.commit()
        inscricao = InscricaoTreinamento(
            turma_id=turma.id,
            nome='João',
            email='joao@example.com',
            cpf='123',
            empresa='Empresa'
        )
        db.session.add(inscricao)
        db.session.commit()
        iid = inscricao.id

    called = {}

    def fake_send_email(to, subject, html):
        called['to'] = to
        called['subject'] = subject
        called['html'] = html

    monkeypatch.setattr(
        'src.services.convocacao_service.send_email', fake_send_email
    )

    resp = client.post(f'/api/inscricoes/{iid}/convocar', headers=headers)
    assert resp.status_code == 200  # nosec B101
    assert called['to'] == 'joao@example.com'  # nosec B101
    assert 'Convocação' in called['subject']  # nosec B101
    with app.app_context():
        insc = db.session.get(InscricaoTreinamento, iid)
        assert insc.convocado_em is not None  # nosec B101
        assert insc.convocado_por.startswith('admin:')  # nosec B101


def test_convocar_todos(client, app, monkeypatch):
    headers = admin_headers(app)
    with app.app_context():
        treino = Treinamento(
            nome='Treino', codigo='T2', carga_horaria=8, tem_pratica=False
        )
        db.session.add(treino)
        db.session.commit()
        turma = TurmaTreinamento(
            treinamento_id=treino.id,
            data_inicio=date.today(),
            data_fim=date.today(),
            local_realizacao='Local',
            horario='08h',
        )
        db.session.add(turma)
        db.session.commit()
        inscs = []
        for i in range(2):
            insc = InscricaoTreinamento(
                turma_id=turma.id,
                nome=f'Pessoa {i}',
                email=f'p{i}@ex.com',
                cpf=str(i),
            )
            db.session.add(insc)
            inscs.append(insc)
        db.session.commit()
        tid = turma.id

    monkeypatch.setattr(
        'src.services.convocacao_service.send_email',
        lambda **kwargs: None,
    )

    resp = client.post(
        f'/api/turmas/{tid}/convocar-todos', headers=headers
    )
    assert resp.status_code == 200  # nosec B101
    assert resp.json['enviados'] == 2  # nosec B101
    assert resp.json['pulados'] == 0  # nosec B101

    resp = client.post(
        f'/api/turmas/{tid}/convocar-todos', headers=headers
    )
    assert resp.json['enviados'] == 0  # nosec B101
    assert resp.json['pulados'] == 2  # nosec B101

    resp = client.post(
        f'/api/turmas/{tid}/convocar-todos',
        headers=headers,
        json={'force': True},
    )
    assert resp.json['enviados'] == 2  # nosec B101
    assert resp.json['pulados'] == 0  # nosec B101
