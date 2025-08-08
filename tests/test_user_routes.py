
import jwt
import uuid
import logging
from datetime import datetime, timedelta
from src.models import db
from src.models.user import User
from src.routes.user import gerar_refresh_token


def fetch_csrf(client):
    return client.get('/api/csrf-token').get_json()['csrf_token']


def test_criar_usuario(client):
    csrf = fetch_csrf(client)
    response = client.post('/api/usuarios', json={
        'nome': 'Novo Usuario',
        'email': 'novo@example.com',
        'senha': 'Senha@123'
    }, headers={'X-CSRFToken': csrf}, environ_base={'REMOTE_ADDR': '1.1.1.10'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['email'] == 'novo@example.com'


def test_criar_usuario_sem_csrf(client):
    resp = client.post(
        '/api/usuarios',
        json={'nome': 'CSRF', 'email': 'csrf@example.com', 'senha': 'Senha@123'},
        environ_base={'REMOTE_ADDR': '1.1.1.16'}
    )
    assert resp.status_code == 400


def test_criar_usuario_senha_invalida(client):
    csrf = fetch_csrf(client)
    resp = client.post(
        '/api/usuarios',
        json={'nome': 'Fraco', 'email': 'fraco@example.com', 'senha': 'curta'},
        headers={'X-CSRFToken': csrf},
        environ_base={'REMOTE_ADDR': '1.1.1.15'}
    )
    assert resp.status_code == 400
    assert 'erro' in resp.get_json()


def test_login(client):
    csrf = fetch_csrf(client)
    response = client.post(
        '/api/login',
        json={'email': 'admin@example.com', 'senha': 'Password1!'},
        headers={'X-CSRFToken': csrf},
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'token' in json_data
    assert 'refresh_token' in json_data
    assert 'csrf_token' in json_data
    cookies = response.headers.getlist('Set-Cookie')
    assert any('access_token=' in c for c in cookies)
    assert any('refresh_token=' in c for c in cookies)
    assert any('csrf_token=' in c for c in cookies)
    assert all('SameSite=Strict' in c for c in cookies if 'access_token=' in c or 'refresh_token=' in c)


def test_listar_usuarios(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    response = client.get('/api/usuarios', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'items' in data
    assert any(u['email'] == 'admin@example.com' for u in data['items'])


def test_listar_usuarios_paginado(client, login_admin):
    with client.application.app_context():
        for i in range(15):
            db.session.add(User(nome=f'U{i}', email=f'u{i}@example.com', senha='Senha@123', tipo='comum'))
        db.session.commit()

    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client.get('/api/usuarios?page=2&per_page=5', headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['page'] == 2
    assert len(data['items']) == 5


def test_listar_usuarios_per_page_limit(client, login_admin):
    with client.application.app_context():
        for i in range(105):
            db.session.add(User(nome=f'Lim{i}', email=f'lim{i}@example.com', senha='Senha@123', tipo='comum'))
        db.session.commit()

    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client.get('/api/usuarios?per_page=200', headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data['items']) == 100
    assert data['pages'] == 2


def test_refresh_token(client, login_admin):
    token, refresh = login_admin(client)
    csrf = fetch_csrf(client)
    # Expire token by not waiting but calling refresh
    resp = client.post(
        '/api/refresh',
        json={'refresh_token': refresh},
        headers={'X-CSRFToken': csrf},
    )
    assert resp.status_code == 200
    dados = resp.get_json()
    assert 'token' in dados
    assert 'csrf_token' in dados


def test_atualizar_senha_requer_verificacao(client):
    # cria usuario normal
    csrf = fetch_csrf(client)
    resp = client.post('/api/usuarios', json={
        'nome': 'Teste',
        'email': 'teste@example.com',
        'senha': 'Original1!'
    }, headers={'X-CSRFToken': csrf}, environ_base={'REMOTE_ADDR': '1.1.1.11'})
    assert resp.status_code == 201
    user_id = resp.get_json()['id']

    # login como o novo usuario
    csrf = fetch_csrf(client)
    resp_login = client.post(
        '/api/login',
        json={'email': 'teste@example.com', 'senha': 'Original1!'},
        headers={'X-CSRFToken': csrf},
    )
    assert resp_login.status_code == 200
    token = resp_login.get_json()['token']
    headers = {'Authorization': f'Bearer {token}', 'X-CSRFToken': fetch_csrf(client)}

    # Falta senha_atual
    resp_put = client.put(
        f'/api/usuarios/{user_id}',
        json={'senha': 'NovaSeg1!'},
        headers=headers,
    )
    assert resp_put.status_code == 400

    # Senha atual incorreta
    headers['X-CSRFToken'] = fetch_csrf(client)
    resp_put = client.put(
        f'/api/usuarios/{user_id}',
        json={'senha': 'NovaSeg1!', 'senha_atual': 'Errada1!'},
        headers=headers,
    )
    assert resp_put.status_code == 403

    # Senha atual correta
    headers['X-CSRFToken'] = fetch_csrf(client)
    resp_put = client.put(
        f'/api/usuarios/{user_id}',
        json={'senha': 'NovaSeg1!', 'senha_atual': 'Original1!'},
        headers=headers,
    )
    assert resp_put.status_code == 200

    # login com nova senha deve funcionar
    csrf = fetch_csrf(client)
    resp_login2 = client.post(
        '/api/login',
        json={'email': 'teste@example.com', 'senha': 'NovaSeg1!'},
        headers={'X-CSRFToken': csrf},
    )
    assert resp_login2.status_code == 200


def test_criar_usuario_dados_incompletos(client):
    csrf = fetch_csrf(client)
    resp = client.post(
        '/api/usuarios',
        json={'nome': 'Incompleto'},
        headers={'X-CSRFToken': csrf},
        environ_base={'REMOTE_ADDR': '1.1.1.1'}
    )
    assert resp.status_code == 400
    assert 'erro' in resp.get_json()


def test_criar_usuario_duplicado(client):
    csrf = fetch_csrf(client)
    resp1 = client.post('/api/usuarios', json={
        'nome': 'Dup',
        'email': 'dup@example.com',
        'senha': 'Dup#1234'
    }, headers={'X-CSRFToken': csrf}, environ_base={'REMOTE_ADDR': '1.1.1.2'})
    assert resp1.status_code == 201
    csrf = fetch_csrf(client)
    resp2 = client.post('/api/usuarios', json={
        'nome': 'Outro',
        'email': 'dup@example.com',
        'senha': 'Dup#4321'
    }, headers={'X-CSRFToken': csrf}, environ_base={'REMOTE_ADDR': '1.1.1.3'})
    assert resp2.status_code == 400


def test_atualizar_usuario_tipo_invalido(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    csrf = fetch_csrf(client)
    resp = client.post('/api/usuarios', json={
        'nome': 'Tipo',
        'email': 'tipo@example.com',
        'senha': 'Tipo@123'
    }, headers={'X-CSRFToken': csrf}, environ_base={'REMOTE_ADDR': '1.1.1.4'})
    assert resp.status_code == 201
    user_id = resp.get_json()['id']
    headers['X-CSRFToken'] = fetch_csrf(client)
    resp_put = client.put(
        f'/api/usuarios/{user_id}',
        json={'tipo': 'super'},
        headers=headers,
    )
    assert resp_put.status_code == 400


def test_login_dados_incompletos(client):
    csrf = fetch_csrf(client)
    resp = client.post(
        '/api/login',
        json={'email': 'admin@example.com'},
        headers={'X-CSRFToken': csrf},
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['success'] is False
    assert 'message' in data


def test_login_invalido(client, caplog):
    with caplog.at_level(logging.WARNING):
        csrf = fetch_csrf(client)
        resp = client.post(
            '/api/login',
            json={'email': 'admin@example.com', 'senha': 'errada'},
            headers={'X-CSRFToken': csrf},
            environ_base={'REMOTE_ADDR': '2.2.2.2'},
        )
    assert resp.status_code == 401
    data = resp.get_json()
    assert data['success'] is False
    assert 'message' in data
    assert any('2.2.2.2' in rec.getMessage() for rec in caplog.records)


def test_refresh_sem_token(client):
    csrf = fetch_csrf(client)
    resp = client.post('/api/refresh', json={}, headers={'X-CSRFToken': csrf})
    assert resp.status_code == 400


def test_logout_sem_token(client):
    csrf = fetch_csrf(client)
    resp = client.post('/api/logout', json={}, headers={'X-CSRFToken': csrf})
    assert resp.status_code == 400


def test_logout_com_token_expirado(client):
    with client.application.app_context():
        user = User.query.filter_by(email='admin@example.com').first()
        expired_token = jwt.encode(
            {
                'user_id': user.id,
                'nome': user.nome,
                'perfil': user.tipo,
                'exp': datetime.utcnow() - timedelta(minutes=5),
                'jti': str(uuid.uuid4()),
            },
            client.application.config['SECRET_KEY'],
            algorithm='HS256',
        )
        refresh = gerar_refresh_token(user)

    headers = {'Authorization': f'Bearer {expired_token}', 'X-CSRFToken': fetch_csrf(client)}
    resp = client.post('/api/logout', headers=headers, json={'refresh_token': refresh})
    assert resp.status_code == 200


def test_atualizar_usuario_senha_invalida(client):
    csrf = fetch_csrf(client)
    resp = client.post('/api/usuarios', json={
        'nome': 'Complex',
        'email': 'complex@example.com',
        'senha': 'Valida1!'
    }, headers={'X-CSRFToken': csrf}, environ_base={'REMOTE_ADDR': '1.1.1.12'})
    assert resp.status_code == 201
    user_id = resp.get_json()['id']

    csrf = fetch_csrf(client)
    resp_login = client.post(
        '/api/login',
        json={'email': 'complex@example.com', 'senha': 'Valida1!'},
        headers={'X-CSRFToken': csrf},
    )
    token = resp_login.get_json()['token']
    headers = {'Authorization': f'Bearer {token}', 'X-CSRFToken': fetch_csrf(client)}

    resp_put = client.put(
        f'/api/usuarios/{user_id}',
        json={'senha': 'fraca', 'senha_atual': 'Valida1!'},
        headers=headers,
    )
    assert resp_put.status_code == 400
    assert 'erro' in resp_put.get_json()


def test_non_root_admin_cannot_downgrade_admin(client, login_admin):
    # Root admin cria outro usuario e promove a admin
    token_root, _ = login_admin(client)
    headers_root = {'Authorization': f'Bearer {token_root}', 'X-CSRFToken': fetch_csrf(client)}

    csrf = fetch_csrf(client)
    resp_create = client.post(
        '/api/usuarios',
        json={'nome': 'Outro', 'email': 'outro@example.com', 'senha': 'Senha@123'},
        headers={'X-CSRFToken': csrf},
        environ_base={'REMOTE_ADDR': '1.1.1.13'},
    )
    assert resp_create.status_code == 201
    novo_id = resp_create.get_json()['id']

    headers_root['X-CSRFToken'] = fetch_csrf(client)
    resp_promote = client.put(
        f'/api/usuarios/{novo_id}', json={'tipo': 'admin'}, headers=headers_root
    )
    assert resp_promote.status_code == 200

    csrf = fetch_csrf(client)
    resp_login = client.post(
        '/api/login',
        json={'email': 'outro@example.com', 'senha': 'Senha@123'},
        headers={'X-CSRFToken': csrf},
    )
    token_new = resp_login.get_json()['token']
    headers_new = {'Authorization': f'Bearer {token_new}', 'X-CSRFToken': fetch_csrf(client)}

    with client.application.app_context():
        root_id = User.query.filter_by(email='admin@example.com').first().id

    resp_downgrade = client.put(
        f'/api/usuarios/{root_id}', json={'tipo': 'comum'}, headers=headers_new
    )
    assert resp_downgrade.status_code == 403


def test_root_admin_can_downgrade_admin(client, login_admin):
    token_root, _ = login_admin(client)
    headers_root = {'Authorization': f'Bearer {token_root}', 'X-CSRFToken': fetch_csrf(client)}

    csrf = fetch_csrf(client)
    resp_create = client.post(
        '/api/usuarios',
        json={'nome': 'Temp', 'email': 'temp@example.com', 'senha': 'Senha@123'},
        headers={'X-CSRFToken': csrf},
        environ_base={'REMOTE_ADDR': '1.1.1.14'},
    )
    assert resp_create.status_code == 201
    admin_id = resp_create.get_json()['id']

    headers_root['X-CSRFToken'] = fetch_csrf(client)
    resp_promote = client.put(
        f'/api/usuarios/{admin_id}', json={'tipo': 'admin'}, headers=headers_root
    )
    assert resp_promote.status_code == 200

    headers_root['X-CSRFToken'] = fetch_csrf(client)
    resp_downgrade = client.put(
        f'/api/usuarios/{admin_id}', json={'tipo': 'comum'}, headers=headers_root
    )
    assert resp_downgrade.status_code == 200
    assert resp_downgrade.get_json()['tipo'] == 'comum'


def test_non_root_admin_cannot_delete_admin(client, login_admin):
    token_root, _ = login_admin(client)
    headers_root = {'Authorization': f'Bearer {token_root}', 'X-CSRFToken': fetch_csrf(client)}

    csrf = fetch_csrf(client)
    resp_create = client.post(
        '/api/usuarios',
        json={'nome': 'Admin2', 'email': 'admin2@example.com', 'senha': 'Senha@123'},
        headers={'X-CSRFToken': csrf},
        environ_base={'REMOTE_ADDR': '1.1.1.18'},
    )
    assert resp_create.status_code == 201
    admin2_id = resp_create.get_json()['id']

    headers_root['X-CSRFToken'] = fetch_csrf(client)
    resp_promote = client.put(
        f'/api/usuarios/{admin2_id}', json={'tipo': 'admin'}, headers=headers_root
    )
    assert resp_promote.status_code == 200

    csrf = fetch_csrf(client)
    resp_login = client.post(
        '/api/login',
        json={'email': 'admin2@example.com', 'senha': 'Senha@123'},
        headers={'X-CSRFToken': csrf},
    )
    assert resp_login.status_code == 200
    token_admin2 = resp_login.get_json()['token']
    headers_admin2 = {'Authorization': f'Bearer {token_admin2}', 'X-CSRFToken': fetch_csrf(client)}

    with client.application.app_context():
        root_id = User.query.filter_by(email='admin@example.com').first().id

    resp_delete = client.delete(f'/api/usuarios/{root_id}', headers=headers_admin2)
    assert resp_delete.status_code == 403


def test_root_admin_can_delete_admin(client, login_admin):
    token_root, _ = login_admin(client)
    headers_root = {'Authorization': f'Bearer {token_root}', 'X-CSRFToken': fetch_csrf(client)}

    csrf = fetch_csrf(client)
    resp_create = client.post(
        '/api/usuarios',
        json={'nome': 'Admin3', 'email': 'admin3@example.com', 'senha': 'Senha@123'},
        headers={'X-CSRFToken': csrf},
        environ_base={'REMOTE_ADDR': '1.1.1.19'},
    )
    assert resp_create.status_code == 201
    admin3_id = resp_create.get_json()['id']

    headers_root['X-CSRFToken'] = fetch_csrf(client)
    resp_promote = client.put(
        f'/api/usuarios/{admin3_id}', json={'tipo': 'admin'}, headers=headers_root
    )
    assert resp_promote.status_code == 200

    headers_root['X-CSRFToken'] = fetch_csrf(client)
    resp_delete = client.delete(f'/api/usuarios/{admin3_id}', headers=headers_root)
    assert resp_delete.status_code == 200
    assert resp_delete.get_json()['mensagem'] == 'Usuário removido com sucesso'
