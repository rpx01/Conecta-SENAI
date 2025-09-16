import pytest
from conectasenai_api.models import db
from conectasenai_api.models.planejamento import (
    Horario,
    CargaHoraria,
    Modalidade,
    PlanejamentoTreinamento,
    Local,
    PublicoAlvo,
)
from conectasenai_api.models.instrutor import Instrutor


def auth_headers(client, login_admin, csrf_token):
    token, _ = login_admin(client)
    return {
        'Authorization': f'Bearer {token}',
        'X-CSRF-Token': csrf_token,
    }


@pytest.fixture
def base_ids(app):
    with app.app_context():
        horario = Horario(nome='Manhã', turno='Manhã')
        carga = CargaHoraria(nome='8h')
        modalidade = Modalidade(nome='Presencial')
        treinamento = PlanejamentoTreinamento(nome='Treinamento X')
        instrutor = Instrutor(nome='Instrutor X')
        local = Local(nome='Sala X')
        cmd = PublicoAlvo(nome='CMD')
        sjb = PublicoAlvo(nome='SJB')
        sag = PublicoAlvo(nome='SAG/TOMBOS')
        db.session.add_all([horario, carga, modalidade, treinamento, instrutor, local, cmd, sjb, sag])
        db.session.commit()
        return {
            'horario_id': horario.id,
            'carga_horaria_id': carga.id,
            'modalidade_id': modalidade.id,
            'treinamento_id': treinamento.id,
            'instrutor_id': instrutor.id,
            'local_id': local.id,
            'cmd_id': cmd.id,
            'sjb_id': sjb.id,
            'sag_tombos_id': sag.id,
        }


def test_post_planejamentos_201(client, base_ids, login_admin, csrf_token):
    headers = auth_headers(client, login_admin, csrf_token)
    payload = {
        'data_inicial': '2024-01-01',
        'data_final': '2024-01-02',
        **base_ids,
    }
    resp = client.post('/api/planejamentos', json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert 'id' in data


def test_post_planejamentos_ids_string_422(client, base_ids, login_admin, csrf_token):
    headers = auth_headers(client, login_admin, csrf_token)
    payload = {
        'data_inicial': '2024-01-01',
        'data_final': '2024-01-02',
        **base_ids,
    }
    payload['horario_id'] = str(payload['horario_id'])
    resp = client.post('/api/planejamentos', json=payload, headers=headers)
    assert resp.status_code == 422
