import jwt
from datetime import datetime, timedelta
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


def test_criar_e_atualizar_treinamento(client, app):
    headers = admin_headers(app)
    resp = client.post('/api/treinamentos/catalogo', json={
        'nome': 'Trein',
        'codigo': 'T1',
        'conteudo_programatico': 'Intro'
    }, headers=headers)
    assert resp.status_code == 201
    treino_id = resp.get_json()['id']
    assert resp.get_json()['conteudo_programatico'] == 'Intro'

    resp_up = client.put(f'/api/treinamentos/catalogo/{treino_id}', json={
        'conteudo_programatico': 'Avancado'
    }, headers=headers)
    assert resp_up.status_code == 200
    assert resp_up.get_json()['conteudo_programatico'] == 'Avancado'

