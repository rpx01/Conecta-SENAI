import pytest

from conecta_senai.models import db
from conecta_senai.models.suporte_basedados import SuporteArea, SuporteTipoEquipamento
from conecta_senai.models.suporte_chamado import SuporteChamado


@pytest.fixture
def suporte_base(app):
    with app.app_context():
        area = SuporteArea(nome='Infraestrutura')
        tipo = SuporteTipoEquipamento(nome='Notebook')
        db.session.add_all([area, tipo])
        db.session.commit()
        return {
            'area_nome': area.nome,
            'tipo_id': tipo.id,
        }


def test_abertura_chamado_limita_campos_texto(client, app, csrf_token, suporte_base):
    email = 'usuario.extenso.' + ('a' * 100) + '@example.com' + ('b' * 40)

    resposta = client.post(
        '/suporte/abrir-chamado',
        data={
            'csrf_token': csrf_token,
            'nome_completo': 'Visitante Teste',
            'email': email,
            'area': suporte_base['area_nome'],
            'tipo_equipamento_id': suporte_base['tipo_id'],
            'descricao_problema': 'Computador não liga.',
            'nivel_urgencia': 'Medio',
        },
    )

    assert resposta.status_code == 201
    payload = resposta.get_json()
    assert payload['mensagem']

    with app.app_context():
        chamado = SuporteChamado.query.get(payload['id'])
        email_max_len = SuporteChamado.email.property.columns[0].type.length
        area_max_len = SuporteChamado.area.property.columns[0].type.length
        assert len(chamado.email) == email_max_len
        assert len(chamado.area) <= area_max_len
        assert chamado.nivel_urgencia == 'Médio'


def test_abertura_chamado_token_invalido(client, suporte_base):
    resposta = client.post(
        '/suporte/abrir-chamado',
        data={
            'csrf_token': 'token-invalido',
            'nome_completo': 'Visitante Teste',
            'email': 'visitante@example.com',
            'area': suporte_base['area_nome'],
            'tipo_equipamento_id': suporte_base['tipo_id'],
            'descricao_problema': 'Sem acesso à rede.',
        },
    )

    assert resposta.status_code == 400
    assert resposta.get_json()['erro'] == 'Token CSRF inválido.'
