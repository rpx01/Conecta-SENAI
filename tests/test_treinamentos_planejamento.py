from datetime import datetime, timedelta
import jwt

from src.models.user import User


def admin_headers(app):
    with app.app_context():
        user = User.query.filter_by(email='admin@example.com').first()
        token = jwt.encode({
            'user_id': user.id,
            'nome': user.nome,
            'perfil': user.tipo,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return {'Authorization': f'Bearer {token}'}


def test_get_treinamentos_planejamento(client, app):
    headers = admin_headers(app)
    resp_create = client.post(
        '/api/treinamentos/catalogo',
        json={'nome': 'Treino P', 'codigo': 'TP'},
        headers=headers
    )
    assert resp_create.status_code == 201  # nosec B101

    resp = client.get('/api/treinamentos_planejamento', headers=headers)
    assert resp.status_code == 200  # nosec B101
    data = resp.get_json()
    assert 'itens' in data  # nosec B101
    assert any(t['nome'] == 'Treino P' for t in data['itens'])  # nosec B101
