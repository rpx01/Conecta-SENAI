from datetime import datetime, timedelta
import jwt
from src.models.user import User


def admin_headers(app):
    with app.app_context():
        user = User.query.filter_by(email='admin@example.com').first()
        token = jwt.encode({'user_id': user.id, 'nome': user.nome, 'perfil': user.tipo,
                             'exp': datetime.utcnow() + timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm='HS256')
    return {'Authorization': f'Bearer {token}'}


def test_criar_listar_centro_custo(client, app):
    headers = admin_headers(app)
    resp = client.post('/api/centros-custo', json={'nome': 'TI', 'descricao': 'Informatica'}, headers=headers)
    assert resp.status_code == 201
    cc_id = resp.get_json()['id']

    lista = client.get('/api/centros-custo', headers=headers)
    assert lista.status_code == 200
    assert any(cc['id'] == cc_id for cc in lista.get_json())


def test_criar_centro_custo_nao_admin(client, non_admin_auth_headers):
    resp = client.post('/api/centros-custo', json={'nome': 'X'}, headers=non_admin_auth_headers)
    assert resp.status_code == 403
