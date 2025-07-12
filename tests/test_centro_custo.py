from src.models.centro_custo import CentroCusto


def test_criar_listar_centro_custo(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client.post('/api/centros-custo', json={'nome': 'Projeto X'}, headers=headers)
    assert resp.status_code == 201
    cid = resp.get_json()['id']

    resp = client.get('/api/centros-custo', headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert any(c['id'] == cid for c in data)


def test_centro_custo_non_admin_forbidden(client, non_admin_auth_headers):
    resp = client.post('/api/centros-custo', json={'nome': 'P'}, headers=non_admin_auth_headers)
    assert resp.status_code == 403
