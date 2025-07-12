from src.models.instrutor import Instrutor
from src.models.centro_custo import CentroCusto
from src.models.apontamento import Apontamento
from src.models import db


def test_criar_apontamento(client, app, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    with app.app_context():
        instrutor = Instrutor(nome='A')
        instrutor.custo_hora = 10
        db.session.add(instrutor)
        centro = CentroCusto(nome='CC')
        db.session.add(centro)
        db.session.commit()
        instrutor_id = instrutor.id
        centro_id = centro.id

    resp = client.post('/api/apontamentos', json={
        'data': '2025-01-01',
        'horas': 2,
        'instrutor_id': instrutor_id,
        'centro_custo_id': centro_id
    }, headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['valor_total'] == 20

    resp = client.get('/api/apontamentos', headers=headers)
    assert resp.status_code == 200

