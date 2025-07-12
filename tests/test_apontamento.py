from datetime import datetime, timedelta
import jwt
from src.models.user import User


def admin_headers(app):
    with app.app_context():
        user = User.query.filter_by(email='admin@example.com').first()
        token = jwt.encode({'user_id': user.id, 'nome': user.nome, 'perfil': user.tipo,
                             'exp': datetime.utcnow() + timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm='HS256')
    return {'Authorization': f'Bearer {token}'}


def test_criar_e_listar_apontamento(client, app):
    headers = admin_headers(app)
    cc = client.post('/api/centros-custo', json={'nome': 'CC'}, headers=headers).get_json()
    instr = client.post('/api/instrutores', json={'nome': 'Inst'}, headers=headers).get_json()

    resp = client.post('/api/apontamentos', json={
        'data': '2024-01-01',
        'horas': 2,
        'descricao': 'Teste',
        'instrutor_id': instr['id'],
        'centro_custo_id': cc['id']
    }, headers=headers)
    assert resp.status_code == 201
    ap_id = resp.get_json()['id']

    lista = client.get('/api/apontamentos', headers=headers)
    assert any(a['id'] == ap_id for a in lista.get_json())
