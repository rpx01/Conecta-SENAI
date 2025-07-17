def test_criar_treinamento(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client.post('/api/treinamentos', json={
        'nome': 'NR-35 Trabalho em Altura',
        'codigo': 'NR35',
        'carga_horaria': 8
    }, headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['nome'] == 'NR-35 Trabalho em Altura'


def test_listar_treinamentos_requer_login(client):
    resp = client.get('/api/treinamentos')
    assert resp.status_code == 401
