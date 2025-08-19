import pytest
from datetime import date
from uuid import uuid4

from src.models import db
from src.models.treinamento import Treinamento
from src.models.instrutor import Instrutor
from src.models.planejamento import PlanejamentoItem


@pytest.fixture
def setup_dados(app):
    with app.app_context():
        t = Treinamento(nome='T1', codigo='T1')
        i = Instrutor(nome='Instrutor 1')
        db.session.add_all([t, i])
        db.session.commit()
        return t.nome, i.nome


def auth_headers(client, login_admin, csrf_token):
    token, _ = login_admin(client)
    return {
        'Authorization': f'Bearer {token}',
        'X-CSRF-Token': csrf_token
    }


def test_422_sem_treinamento(client, setup_dados, login_admin, csrf_token):
    _, instrutor_nome = setup_dados
    payload = {
        'registros': [{
            'inicio': '2024-01-01',
            'fim': '2024-01-01',
            'semana': '1',
            'horario': '08:00',
            'carga_horaria': 8,
            'modalidade': 'P',
            'polos': {'cmd': True, 'sjb': False, 'sag_tombos': False},
            'instrutor': instrutor_nome,
            'local': '',
            'observacao': ''
        }]
    }
    headers = auth_headers(client, login_admin, csrf_token)
    resp = client.post('/api/planejamento', json=payload, headers=headers)
    assert resp.status_code == 422
    data = resp.get_json()
    assert 'treinamento' in data['detalhes']


def test_422_inicio_maior_que_fim(
    client, setup_dados, login_admin, csrf_token
):
    treinamento_nome, instrutor_nome = setup_dados
    payload = {
        'registros': [{
            'inicio': '2024-02-10',
            'fim': '2024-02-01',
            'semana': '1',
            'horario': '08:00',
            'carga_horaria': 8,
            'modalidade': 'P',
            'treinamento': treinamento_nome,
            'polos': {'cmd': True, 'sjb': False, 'sag_tombos': False},
            'instrutor': instrutor_nome,
            'local': '',
            'observacao': ''
        }]
    }
    headers = auth_headers(client, login_admin, csrf_token)
    resp = client.post('/api/planejamento', json=payload, headers=headers)
    assert resp.status_code == 422


def test_201_tres_registros_validos(
    client, setup_dados, login_admin, csrf_token
):
    treinamento_nome, instrutor_nome = setup_dados
    registros = []
    for dia in range(1, 4):
        registros.append({
            'inicio': f'2024-03-0{dia}',
            'fim': f'2024-03-0{dia}',
            'semana': '1',
            'horario': '08:00',
            'carga_horaria': 8,
            'modalidade': 'P',
            'treinamento': treinamento_nome,
            'polos': {'cmd': True, 'sjb': False, 'sag_tombos': False},
            'instrutor': instrutor_nome,
            'local': '',
            'observacao': ''
        })
    payload = {'registros': registros}
    headers = auth_headers(client, login_admin, csrf_token)
    resp = client.post('/api/planejamento', json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['quantidade'] == 3


def test_sem_csrf_retorna_403(client, setup_dados, login_admin):
    treinamento_nome, instrutor_nome = setup_dados
    payload = {
        'registros': [{
            'inicio': '2024-01-01',
            'fim': '2024-01-01',
            'semana': '1',
            'horario': '08:00',
            'carga_horaria': 8,
            'modalidade': 'P',
            'treinamento': treinamento_nome,
            'polos': {'cmd': True, 'sjb': False, 'sag_tombos': False},
            'instrutor': instrutor_nome,
            'local': '',
            'observacao': ''
        }]
    }
    token, _ = login_admin(client)
    resp = client.post(
        '/api/planejamento',
        json=payload,
        headers={'Authorization': f'Bearer {token}'},
    )
    assert resp.status_code == 403


def test_cria_tabela_quando_ausente(
    client, setup_dados, login_admin, csrf_token
):
    treinamento_nome, instrutor_nome = setup_dados
    from src.models.planejamento import PlanejamentoItem
    from src.models import db
    with client.application.app_context():
        PlanejamentoItem.__table__.drop(db.engine)

    payload = {
        'data': '2024-04-01',
        'semana': '1',
        'horario': '08:00',
        'carga_horaria': '8',
        'modalidade': 'P',
        'treinamento': treinamento_nome,
        'cmd': True,
        'sjb': False,
        'sag_tombos': False,
        'instrutor': instrutor_nome,
        'local': '',
        'observacao': ''
    }
    headers = auth_headers(client, login_admin, csrf_token)
    resp = client.post(
        '/api/planejamento/itens', json=payload, headers=headers
    )
    assert resp.status_code == 201


@pytest.fixture
def lote_setup(app):
    with app.app_context():
        t1 = Treinamento(nome='T1', codigo='T1')
        t2 = Treinamento(nome='T2', codigo='T2')
        i1 = Instrutor(nome='Instrutor 1')
        i2 = Instrutor(nome='Instrutor 2')
        db.session.add_all([t1, t2, i1, i2])
        db.session.commit()
        lote_id = str(uuid4())
        row_ids = []
        for dia in range(1, 4):
            item = PlanejamentoItem(
                row_id=str(uuid4()),
                lote_id=lote_id,
                data=date(2024, 1, dia),
                semana='1',
                horario='08:00',
                carga_horaria='8',
                modalidade='P',
                treinamento=t1.nome,
                cmd='True',
                sjb='False',
                sag_tombos='False',
                instrutor=str(i1.id),
                local='',
                observacao='',
            )
            db.session.add(item)
            row_ids.append(item.row_id)
        db.session.commit()
        return {
            'lote_id': lote_id,
            'row_ids': row_ids,
            't2_id': t2.id,
            't2_nome': t2.nome,
            'i1_id': i1.id,
            'i2_id': i2.id,
        }


def test_patch_lote_atualiza_campos(client, lote_setup, login_admin, csrf_token):
    headers = auth_headers(client, login_admin, csrf_token)
    payload = {
        'horario': '09:00',
        'carga_horaria': 10,
        'modalidade': 'E',
        'treinamento_id': lote_setup['t2_id'],
        'polos': {'cmd': False, 'sjb': True, 'sag_tombos': False},
        'local': 'Novo local',
        'observacao': 'Obs',
    }
    resp = client.patch(
        f"/api/planejamento/lote/{lote_setup['lote_id']}",
        json=payload,
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['quantidade'] == len(lote_setup['row_ids'])

    with client.application.app_context():
        itens = PlanejamentoItem.query.filter_by(lote_id=lote_setup['lote_id']).all()
        assert all(it.horario == '09:00' for it in itens)
        assert all(it.carga_horaria == '10' for it in itens)
        assert all(it.modalidade == 'E' for it in itens)
        assert all(it.treinamento == lote_setup['t2_nome'] for it in itens)
        assert all(it.cmd == 'False' for it in itens)
        assert all(it.sjb == 'True' for it in itens)
        assert all(it.sag_tombos == 'False' for it in itens)
        assert all(it.local == 'Novo local' for it in itens)
        assert all(it.observacao == 'Obs' for it in itens)
        assert all(it.instrutor == str(lote_setup['i1_id']) for it in itens)


def test_patch_linha_instrutor(client, lote_setup, login_admin, csrf_token):
    headers = auth_headers(client, login_admin, csrf_token)
    row_id = lote_setup['row_ids'][0]
    payload = {'instrutor_id': lote_setup['i2_id']}
    resp = client.patch(
        f"/api/planejamento/{row_id}", json=payload, headers=headers
    )
    assert resp.status_code == 200

    with client.application.app_context():
        itens = PlanejamentoItem.query.filter_by(lote_id=lote_setup['lote_id']).all()
        atualizados = {it.row_id: it for it in itens}
        assert atualizados[row_id].instrutor == str(lote_setup['i2_id'])
        for rid, item in atualizados.items():
            if rid != row_id:
                assert item.instrutor == str(lote_setup['i1_id'])
