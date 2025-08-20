import pytest
import sqlalchemy as sa
from src.models import db
from src.models.treinamento import Treinamento
from src.models.instrutor import Instrutor


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


def test_atualiza_sge_link(client, setup_dados, login_admin, csrf_token):
    treinamento_nome, instrutor_nome = setup_dados
    headers = auth_headers(client, login_admin, csrf_token)
    payload = {
        'data': '2024-05-01',
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
    resp = client.post('/api/planejamento/itens', json=payload, headers=headers)
    assert resp.status_code == 201
    item_id = resp.get_json()['id']

    update = {'sge_ativo': True, 'sge_link': 'https://exemplo.com'}
    resp = client.put(f'/api/planejamento/itens/{item_id}', json=update, headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['sge_ativo'] is True
    assert data['sge_link'] == 'https://exemplo.com'


def test_adiciona_colunas_sge_quando_ausentes(
    client, setup_dados, login_admin, csrf_token
):
    headers = auth_headers(client, login_admin, csrf_token)

    with client.application.app_context():
        db.session.execute(sa.text('DROP TABLE IF EXISTS planejamento_itens'))
        db.session.execute(
            sa.text(
                'CREATE TABLE planejamento_itens ('
                'id INTEGER PRIMARY KEY, '
                'row_id VARCHAR(36) UNIQUE NOT NULL, '
                'lote_id VARCHAR(36) NOT NULL, '
                'data DATE NOT NULL, '
                'semana VARCHAR(20), '
                'horario VARCHAR(50), '
                'carga_horaria VARCHAR(50), '
                'modalidade VARCHAR(50), '
                'treinamento VARCHAR(100), '
                'cmd VARCHAR(100), '
                'sjb VARCHAR(100), '
                'sag_tombos VARCHAR(100), '
                'instrutor VARCHAR(100), '
                'local VARCHAR(100), '
                'observacao VARCHAR(255), '
                'criado_em DATETIME, '
                'atualizado_em DATETIME'
                ')'
            )
        )

    resp = client.get('/api/planejamento/itens', headers=headers)
    assert resp.status_code == 200

    with client.application.app_context():
        insp = sa.inspect(db.engine)
        cols = {c['name'] for c in insp.get_columns('planejamento_itens')}
        assert 'sge_ativo' in cols
        assert 'sge_link' in cols
