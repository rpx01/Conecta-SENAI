def test_criar_e_listar_apontamento(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    cc = client.post('/api/centros-custo', json={'nome': 'Projeto X'}, headers=headers).get_json()
    inst = client.post('/api/instrutores', json={'nome': 'Inst', 'email': 'i@example.com'}, headers=headers).get_json()
    resp = client.post('/api/apontamentos', json={
        'data': '2024-01-01',
        'horas': 4,
        'instrutor_id': inst['id'],
        'centro_custo_id': cc['id']
    }, headers=headers)
    assert resp.status_code == 201
    aid = resp.get_json()['id']
    lista = client.get('/api/apontamentos', headers=headers)
    assert any(a['id'] == aid for a in lista.get_json())
