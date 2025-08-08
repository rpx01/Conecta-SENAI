def test_listar_logs_rateio_paginado(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client.get('/api/logs-rateio?page=1&per_page=5', headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data['items']) == 5
    assert data['pages'] == 3

    resp2 = client.get('/api/logs-rateio?page=3&per_page=5', headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert len(data2['items']) == 5
