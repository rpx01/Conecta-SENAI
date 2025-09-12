from datetime import date
from unittest.mock import patch

from src.models import (
    db,
    Treinamento,
    TurmaTreinamento,
    Instrutor,
    SecretariaTreinamentos,
)
from src.services.notification_service import (
    build_turma_diff,
    build_turma_snapshot,
    send_new_turma_notifications,
    send_turma_update_notifications,
)


def test_build_turma_diff_simple():
    old = {"instrutor_id": 1, "instrutor_nome": "A", "local_realizacao": "X"}
    new = {"instrutor_id": 2, "instrutor_nome": "B", "local_realizacao": "Y"}
    diffs = build_turma_diff(old, new)
    assert {"campo": "Instrutor", "de": "A", "para": "B"} in diffs
    assert {"campo": "Local", "de": "X", "para": "Y"} in diffs


def test_send_new_turma_notifications(app):
    with app.app_context():
        instrutor = Instrutor(nome="João", email="joao@example.com")
        db.session.add(instrutor)
        treino = Treinamento(nome="Treino", codigo="T1")
        db.session.add(treino)
        db.session.commit()
        turma = TurmaTreinamento(
            treinamento_id=treino.id,
            data_inicio=date.today(),
            data_fim=date.today(),
            local_realizacao="Local",
            horario="08h",
            instrutor_id=instrutor.id,
        )
        db.session.add(turma)
        db.session.add(
            SecretariaTreinamentos(nome="Sec", email="sec@example.com", ativo=True)
        )
        db.session.commit()
        with patch("src.services.notification_service.send_email") as mock_send:
            send_new_turma_notifications(turma.id)
            dests = [call.kwargs["to"] for call in mock_send.call_args_list]
            assert instrutor.email in dests[0]
            assert "sec@example.com" in dests[1]


def test_send_turma_update_notifications_instrutor_change(app):
    with app.app_context():
        inst1 = Instrutor(nome="A", email="a@example.com")
        inst2 = Instrutor(nome="B", email="b@example.com")
        db.session.add_all([inst1, inst2])
        treino = Treinamento(nome="Treino", codigo="T1")
        db.session.add(treino)
        db.session.add(SecretariaTreinamentos(nome="Sec", email="sec@example.com", ativo=True))
        db.session.commit()
        turma = TurmaTreinamento(
            treinamento_id=treino.id,
            data_inicio=date.today(),
            data_fim=date.today(),
            instrutor_id=inst1.id,
        )
        db.session.add(turma)
        db.session.commit()
        before = build_turma_snapshot(turma)
        turma.instrutor_id = inst2.id
        db.session.commit()
        with patch("src.services.notification_service.send_email") as mock_send:
            send_turma_update_notifications(before, turma.id)
            recipients = [call.kwargs["to"] for call in mock_send.call_args_list]
            assert "sec@example.com" in recipients[0]
            assert "a@example.com" in recipients[1]
            assert "b@example.com" in recipients[2]
