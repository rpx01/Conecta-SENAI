import io

import pytest



@pytest.fixture
def user_headers(non_admin_auth_headers):
    return non_admin_auth_headers


@pytest.fixture
def admin_headers(client, login_admin):
    token, _ = login_admin(client)
    return {'Authorization': f'Bearer {token}'}


def test_criar_listar_detalhar_ticket(client, user_headers):
    data = {
        'titulo': 'Problema na impressora',
        'descricao': 'Impressora travando ao imprimir documentos grandes.',
        'categoria_id': '1',
        'prioridade_id': '2',
        'anexos': (io.BytesIO(b'Relatorio de erro'), 'erro.txt'),
    }
    resp = client.post('/api/chamados', data=data, headers=user_headers, content_type='multipart/form-data')
    assert resp.status_code == 201
    ticket = resp.get_json()
    ticket_id = ticket['id']

    lista = client.get('/api/chamados?mine=true', headers=user_headers)
    assert lista.status_code == 200
    itens = lista.get_json()['items']
    assert any(item['id'] == ticket_id for item in itens)

    detalhe = client.get(f'/api/chamados/{ticket_id}', headers=user_headers)
    assert detalhe.status_code == 200
    assert detalhe.get_json()['titulo'] == data['titulo']


def test_comentario_e_anexo(client, user_headers):
    dados = {
        'titulo': 'Mouse com falha',
        'descricao': 'Cursor trava a cada 5 segundos.',
        'categoria_id': '1',
        'prioridade_id': '2',
    }
    resp = client.post('/api/chamados', data=dados, headers=user_headers, content_type='multipart/form-data')
    ticket_id = resp.get_json()['id']

    comentario = client.post(
        f'/api/chamados/{ticket_id}/comentarios',
        json={'mensagem': 'Teste inicial realizado.'},
        headers=user_headers,
    )
    assert comentario.status_code == 201
    assert comentario.get_json()['mensagem'] == 'Teste inicial realizado.'

    anexos = client.post(
        f'/api/chamados/{ticket_id}/anexos',
        data={'anexos': (io.BytesIO(b'Log de teste'), 'log.txt')},
        headers=user_headers,
        content_type='multipart/form-data',
    )
    assert anexos.status_code == 200
    detalhe = client.get(f'/api/chamados/{ticket_id}', headers=user_headers)
    assert len(detalhe.get_json()['anexos']) == 1


def test_admin_lista_e_atualiza(client, user_headers, admin_headers):
    dados = {
        'titulo': 'Computador sem rede',
        'descricao': 'Sem acesso à rede interna.',
        'categoria_id': '1',
        'prioridade_id': '2',
    }
    resp = client.post('/api/chamados', data=dados, headers=user_headers, content_type='multipart/form-data')
    ticket_id = resp.get_json()['id']

    lista_admin = client.get('/api/chamados/abertos', headers=admin_headers)
    assert lista_admin.status_code == 200
    assert any(item['id'] == ticket_id for item in lista_admin.get_json()['items'])

    patch = client.patch(
        f'/api/chamados/{ticket_id}',
        json={'atribuido_id': 1, 'status_id': 2},
        headers=admin_headers,
    )
    assert patch.status_code == 200
    atualizado = patch.get_json()
    assert atualizado['status_id'] == 2
    assert atualizado['atribuido_id'] == 1

    indicadores = client.get('/api/chamados/indicadores', headers=admin_headers)
    assert indicadores.status_code == 200
    dados_ind = indicadores.get_json()
    assert 'por_status' in dados_ind
    assert 'sla' in dados_ind


def test_crud_base_dados(client, admin_headers):
    # cria
    resp = client.post(
        '/api/chamados/base/locations',
        json={'nome': 'Sala 101'},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    registro = resp.get_json()
    item_id = registro['id']

    # patch
    att = client.patch(
        f'/api/chamados/base/locations/{item_id}',
        json={'nome': 'Sala 102'},
        headers=admin_headers,
    )
    assert att.status_code == 200
    assert att.get_json()['nome'] == 'Sala 102'

    # delete
    delecao = client.delete(
        f'/api/chamados/base/locations/{item_id}',
        headers=admin_headers,
    )
    assert delecao.status_code == 204


def test_download_permissao(client, user_headers):
    resp = client.post(
        '/api/chamados',
        data={
            'titulo': 'Backup com erro',
            'descricao': 'Backup não conclui.',
            'categoria_id': '1',
            'prioridade_id': '2',
            'anexos': (io.BytesIO(b'dados'), 'backup.log'),
        },
        headers=user_headers,
        content_type='multipart/form-data',
    )
    ticket_id = resp.get_json()['id']
    detalhe = client.get(f'/api/chamados/{ticket_id}', headers=user_headers).get_json()
    attachment_id = detalhe['anexos'][0]['id']
    download = client.get(f'/api/chamados/{ticket_id}/download/{attachment_id}', headers=user_headers)
    assert download.status_code == 200
    assert download.data
