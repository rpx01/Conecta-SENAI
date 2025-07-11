from datetime import date

def test_crud_centro_custo(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client.post('/api/centros-custo', json={'nome': 'Financeiro'}, headers=headers)
    assert resp.status_code == 201
    cid = resp.get_json()['id']

    resp = client.get('/api/centros-custo', headers=headers)
    assert any(c['id'] == cid for c in resp.get_json())

    resp = client.put(f'/api/centros-custo/{cid}', json={'descricao': 'Depto'}, headers=headers)
    assert resp.status_code == 200

    resp = client.delete(f'/api/centros-custo/{cid}', headers=headers)
    assert resp.status_code == 200
