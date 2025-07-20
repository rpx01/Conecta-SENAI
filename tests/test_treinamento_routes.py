import pytest


def test_criar_e_listar_treinamento(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client.post('/api/treinamentos', json={
        'nome': 'Python Basico',
        'codigo': 'PY001',
        'carga_horaria': 20,
        'max_alunos': 30,
        'materiais': 'Apostila'
    }, headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['nome'] == 'Python Basico'

    resp = client.get('/api/treinamentos')
    assert resp.status_code == 200
    lista = resp.get_json()
    assert any(t['nome'] == 'Python Basico' for t in lista)


def test_criar_treinamento_dados_invalidos(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client.post('/api/treinamentos', json={'nome': 'Invalido'}, headers=headers)
    assert resp.status_code == 400


def test_criar_treinamento_nao_admin(client, non_admin_auth_headers):
    resp = client.post('/api/treinamentos', json={
        'nome': 'X',
        'carga_horaria': 10,
        'max_alunos': 5
    }, headers=non_admin_auth_headers)
    assert resp.status_code == 403
