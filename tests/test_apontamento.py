from datetime import date


def test_criar_listar_apontamento(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    # pega instrutor e centro custo padrões criados no fixture
    resp_instr = client.get('/api/instrutores', headers=headers)
    instr_id = resp_instr.get_json()[0]['id']
    resp_cc = client.get('/api/centros-custo', headers=headers)
    cc_id = resp_cc.get_json()[0]['id']

    resp = client.post(
        '/api/apontamentos',
        json={
            'data': date.today().isoformat(),
            'horas': 2,
            'descricao': 'Aula',
            'instrutor_id': instr_id,
            'centro_custo_id': cc_id,
        },
        headers=headers,
    )
    assert resp.status_code == 201

    resp = client.get('/api/apontamentos', headers=headers)
    dados = resp.get_json()
    assert any(a['instrutor_id'] == instr_id for a in dados)
