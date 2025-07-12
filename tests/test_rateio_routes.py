import jwt
from datetime import datetime, timedelta
from src.models.user import User


def admin_headers(app):
    with app.app_context():
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


def financeiro_headers(app):
    with app.app_context():
        user = User.query.filter_by(email='financeiro@example.com').first()
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


def test_parametro_crud(client, app):
    headers = admin_headers(app)
    resp = client.post(
        '/api/rateio/parametros',
        json={'filial': 'F1', 'uo': 'U1', 'cr': 'CR1', 'classe_valor': 'A'},
        headers=headers,
    )
    assert resp.status_code == 201
    pid = resp.get_json()['id']

    resp = client.get('/api/rateio/parametros', headers=headers)
    assert resp.status_code == 200
    assert any(p['id'] == pid for p in resp.get_json())

    resp = client.put(
        f'/api/rateio/parametros/{pid}',
        json={'classe_valor': 'B'},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.get_json()['classe_valor'] == 'B'

    resp = client.delete(f'/api/rateio/parametros/{pid}', headers=headers)
    assert resp.status_code == 200


def test_parametro_permission(client, app, non_admin_auth_headers):
    resp = client.post(
        '/api/rateio/parametros',
        json={'filial': 'F1', 'uo': 'U1', 'cr': 'CR1', 'classe_valor': 'A'},
        headers=non_admin_auth_headers,
    )
    assert resp.status_code == 403


def test_lancamento_duplicate(client, app):
    headers = admin_headers(app)
    # create parametro and instrutor
    p = client.post(
        '/api/rateio/parametros',
        json={'filial': 'F1', 'uo': 'U1', 'cr': 'CR1', 'classe_valor': 'A'},
        headers=headers,
    ).get_json()
    inst_resp = client.post('/api/instrutores', json={'nome': 'Inst'}, headers=headers)
    assert inst_resp.status_code == 201
    instr_id = inst_resp.get_json()['id']

    data = {
        'instrutor_id': instr_id,
        'parametro_id': p['id'],
        'data_referencia': '2024-05-10',
        'valor_total': 100.0,
        'horas_trabalhadas': 10.0,
    }
    r1 = client.post('/api/rateio/lancamentos', json=data, headers=headers)
    assert r1.status_code == 201
    r2 = client.post('/api/rateio/lancamentos', json=data, headers=headers)
    assert r2.status_code == 400
