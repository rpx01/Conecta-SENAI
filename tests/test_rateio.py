from datetime import date


def test_relatorio_rateio(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    resp_instr = client.get('/api/instrutores', headers=headers)
    instr_id = resp_instr.get_json()[0]['id']
    resp_cc = client.get('/api/centros-custo', headers=headers)
    cc_id = resp_cc.get_json()[0]['id']

    client.post(
        '/api/apontamentos',
        json={
            'data': date(2024, 1, 15).isoformat(),
            'horas': 3,
            'descricao': 'Ativ',
            'instrutor_id': instr_id,
            'centro_custo_id': cc_id,
        },
        headers=headers,
    )
    client.post(
        '/api/apontamentos',
        json={
            'data': date(2024, 1, 20).isoformat(),
            'horas': 2,
            'descricao': 'Ativ2',
            'instrutor_id': instr_id,
            'centro_custo_id': cc_id,
        },
        headers=headers,
    )

    resp = client.get('/api/rateio/relatorio', query_string={'mes': 1, 'ano': 2024}, headers=headers)
    assert resp.status_code == 200
    dados = resp.get_json()
    assert dados[0]['total_horas'] == 5
