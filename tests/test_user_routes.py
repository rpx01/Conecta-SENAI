
import jwt
import uuid
import logging
from datetime import datetime, timedelta
from src.models.user import User
from src.routes.user import gerar_refresh_token


def test_criar_usuario(client):
    response = client.post('/api/usuarios', json={
        'nome': 'Novo Usuario',
        'email': 'novo@example.com',
        'senha': 'Senha@123'
    }, environ_base={'REMOTE_ADDR': '1.1.1.10'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['email'] == 'novo@example.com'


def test_criar_usuario_senha_invalida(client):
    resp = client.post(
        '/api/usuarios',
        json={'nome': 'Fraco', 'email': 'fraco@example.com', 'senha': 'curta'},
        environ_base={'REMOTE_ADDR': '1.1.1.15'}
    )
    assert resp.status_code == 400
    assert 'erro' in resp.get_json()


def test_login(client):
    response = client.post('/api/login', json={'email': 'admin@example.com', 'senha': 'Password1!'})
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'token' in json_data
    assert 'refresh_token' in json_data
    cookies = response.headers.getlist('Set-Cookie')
    assert any('access_token=' in c for c in cookies)
    assert any('refresh_token=' in c for c in cookies)


def test_listar_usuarios(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    response = client.get('/api/usuarios', headers=headers)
    assert response.status_code == 200
    usuarios = response.get_json()
    assert any(u['email'] == 'admin@example.com' for u in usuarios)


def test_refresh_token(client, login_admin):
    token, refresh = login_admin(client)
    # Expire token by not waiting but calling refresh
    resp = client.post('/api/refresh', json={'refresh_token': refresh})
    assert resp.status_code == 200
    dados = resp.get_json()
    assert 'token' in dados


def test_atualizar_senha_requer_verificacao(client):
    # cria usuario normal
    resp = client.post('/api/usuarios', json={
        'nome': 'Teste',
        'email': 'teste@example.com',
        'senha': 'Original1!'
    }, environ_base={'REMOTE_ADDR': '1.1.1.11'})
    assert resp.status_code == 201
    user_id = resp.get_json()['id']

    # login como o novo usuario
    resp_login = client.post('/api/login', json={'email': 'teste@example.com', 'senha': 'Original1!'})
    assert resp_login.status_code == 200
    token = resp_login.get_json()['token']
    headers = {'Authorization': f'Bearer {token}'}

    # Falta senha_atual
    resp_put = client.put(f'/api/usuarios/{user_id}', json={'senha': 'NovaSeg1!'}, headers=headers)
    assert resp_put.status_code == 400

    # Senha atual incorreta
    resp_put = client.put(
        f'/api/usuarios/{user_id}',
        json={'senha': 'NovaSeg1!', 'senha_atual': 'Errada1!'},
        headers=headers,
    )
    assert resp_put.status_code == 403

    # Senha atual correta
    resp_put = client.put(
        f'/api/usuarios/{user_id}',
        json={'senha': 'NovaSeg1!', 'senha_atual': 'Original1!'},
        headers=headers,
    )
    assert resp_put.status_code == 200

    # login com nova senha deve funcionar
    resp_login2 = client.post('/api/login', json={'email': 'teste@example.com', 'senha': 'NovaSeg1!'})
    assert resp_login2.status_code == 200


def test_criar_usuario_dados_incompletos(client):
    resp = client.post(
        '/api/usuarios',
        json={'nome': 'Incompleto'},
        environ_base={'REMOTE_ADDR': '1.1.1.1'}
    )
    assert resp.status_code == 400
    assert 'erro' in resp.get_json()


def test_criar_usuario_duplicado(client):
    resp1 = client.post('/api/usuarios', json={
        'nome': 'Dup',
        'email': 'dup@example.com',
        'senha': 'Dup#1234'
    }, environ_base={'REMOTE_ADDR': '1.1.1.2'})
    assert resp1.status_code == 201
    resp2 = client.post('/api/usuarios', json={
        'nome': 'Outro',
        'email': 'dup@example.com',
        'senha': 'Dup#4321'
    }, environ_base={'REMOTE_ADDR': '1.1.1.3'})
    assert resp2.status_code == 400


def test_atualizar_usuario_tipo_invalido(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client.post('/api/usuarios', json={
        'nome': 'Tipo',
        'email': 'tipo@example.com',
        'senha': 'Tipo@123'
    }, environ_base={'REMOTE_ADDR': '1.1.1.4'})
    assert resp.status_code == 201
    user_id = resp.get_json()['id']
    resp_put = client.put(f'/api/usuarios/{user_id}', json={'tipo': 'super'}, headers=headers)
    assert resp_put.status_code == 400


def test_login_dados_incompletos(client):
    resp = client.post('/api/login', json={'email': 'admin@example.com'})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['success'] is False
    assert 'message' in data


def test_login_invalido(client, caplog):
    with caplog.at_level(logging.WARNING):
        resp = client.post(
            '/api/login',
            json={'email': 'admin@example.com', 'senha': 'errada'},
            environ_base={'REMOTE_ADDR': '2.2.2.2'},
        )
    assert resp.status_code == 401
    data = resp.get_json()
    assert data['success'] is False
    assert 'message' in data
    assert any('2.2.2.2' in rec.getMessage() for rec in caplog.records)


def test_refresh_sem_token(client):
    resp = client.post('/api/refresh', json={})
    assert resp.status_code == 400


def test_logout_sem_token(client):
    resp = client.post('/api/logout', json={})
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

    headers = {'Authorization': f'Bearer {expired_token}'}
    resp = client.post('/api/logout', headers=headers, json={'refresh_token': refresh})
    assert resp.status_code == 200


def test_atualizar_usuario_senha_invalida(client):
    resp = client.post('/api/usuarios', json={
        'nome': 'Complex',
        'email': 'complex@example.com',
        'senha': 'Valida1!'
    }, environ_base={'REMOTE_ADDR': '1.1.1.12'})
    assert resp.status_code == 201
    user_id = resp.get_json()['id']

    resp_login = client.post('/api/login', json={'email': 'complex@example.com', 'senha': 'Valida1!'})
    token = resp_login.get_json()['token']
    headers = {'Authorization': f'Bearer {token}'}

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
    headers_root = {'Authorization': f'Bearer {token_root}'}

    resp_create = client.post(
        '/api/usuarios',
        json={'nome': 'Outro', 'email': 'outro@example.com', 'senha': 'Senha@123'},
        environ_base={'REMOTE_ADDR': '1.1.1.13'},
    )
    assert resp_create.status_code == 201
    novo_id = resp_create.get_json()['id']

    resp_promote = client.put(
        f'/api/usuarios/{novo_id}', json={'tipo': 'admin'}, headers=headers_root
    )
    assert resp_promote.status_code == 200

    resp_login = client.post(
        '/api/login', json={'email': 'outro@example.com', 'senha': 'Senha@123'}
    )
    token_new = resp_login.get_json()['token']
    headers_new = {'Authorization': f'Bearer {token_new}'}

    with client.application.app_context():
        root_id = User.query.filter_by(email='admin@example.com').first().id

    resp_downgrade = client.put(
        f'/api/usuarios/{root_id}', json={'tipo': 'comum'}, headers=headers_new
    )
    assert resp_downgrade.status_code == 403


def test_root_admin_can_downgrade_admin(client, login_admin):
    token_root, _ = login_admin(client)
    headers_root = {'Authorization': f'Bearer {token_root}'}

    resp_create = client.post(
        '/api/usuarios',
        json={'nome': 'Temp', 'email': 'temp@example.com', 'senha': 'Senha@123'},
        environ_base={'REMOTE_ADDR': '1.1.1.14'},
    )
    assert resp_create.status_code == 201
    admin_id = resp_create.get_json()['id']

    resp_promote = client.put(
        f'/api/usuarios/{admin_id}', json={'tipo': 'admin'}, headers=headers_root
    )
    assert resp_promote.status_code == 200

    resp_downgrade = client.put(
        f'/api/usuarios/{admin_id}', json={'tipo': 'comum'}, headers=headers_root
    )
    assert resp_downgrade.status_code == 200
    assert resp_downgrade.get_json()['tipo'] == 'comum'
