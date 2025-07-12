def test_criar_listar_centro_custo(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client.post('/api/centros-custo', json={'nome': 'Administrativo'}, headers=headers)
    assert resp.status_code == 201
    cid = resp.get_json()['id']

    resp = client.get('/api/centros-custo', headers=headers)
    assert resp.status_code == 200
    dados = resp.get_json()
    assert any(c['id'] == cid for c in dados)
