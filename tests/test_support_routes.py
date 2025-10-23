from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest


@pytest.fixture
def suporte_dados_iniciais(client, csrf_token, login_admin):
    token, _ = login_admin(client)
    admin_headers = {'Authorization': f'Bearer {token}', 'X-CSRF-Token': csrf_token}
    upload_dir = Path(client.application.static_folder) / 'uploads' / 'suporte-ti'
    upload_dir.mkdir(parents=True, exist_ok=True)

    resp_area = client.post(
        '/api/support/areas',
        json={'nome': 'Informática', 'descricao': 'Atendimentos de TI', 'ativo': True},
        headers=admin_headers,
    )
    assert resp_area.status_code == 201
    area_id = resp_area.get_json()['id']

    resp_equip = client.post(
        '/api/support/equipamentos',
        json={'nome': 'Notebook', 'descricao': 'Computadores portáteis', 'ativo': True},
        headers=admin_headers,
    )
    assert resp_equip.status_code == 201
    equipamento_id = resp_equip.get_json()['id']

    yield {
        'csrf_token': csrf_token,
        'admin_headers': admin_headers,
        'area_id': area_id,
        'equipamento_id': equipamento_id,
    }

    if upload_dir.exists():
        for arquivo in upload_dir.iterdir():
            if arquivo.is_file() and arquivo.name != '.gitkeep':
                arquivo.unlink()


def _headers_with_csrf(base_headers: dict[str, str], csrf_token: str) -> dict[str, str]:
    headers = dict(base_headers)
    headers['X-CSRF-Token'] = csrf_token
    return headers


def test_usuario_cria_e_lista_chamados(client, suporte_dados_iniciais, non_admin_auth_headers):
    dados = suporte_dados_iniciais
    csrf_token = dados['csrf_token']

    data = {
        'areaId': str(dados['area_id']),
        'equipamentoId': str(dados['equipamento_id']),
        'patrimonio': 'ABC123',
        'numeroSerie': 'SN-9999',
        'descricao': 'Computador não liga após atualização do sistema operacional.',
        'urgencia': 'alta',
    }
    file_data = (BytesIO(b'imagem-de-teste'), 'foto.png', 'image/png')

    response = client.post(
        '/api/support/tickets',
        data={**data, 'anexos': file_data},
        headers=_headers_with_csrf(non_admin_auth_headers, csrf_token),
        content_type='multipart/form-data',
    )
    assert response.status_code == 201
    ticket = response.get_json()
    assert ticket['area_id'] == dados['area_id']
    assert ticket['equipamento_id'] == dados['equipamento_id']
    assert ticket['urgencia'] == 'alta'
    assert len(ticket['anexos']) == 1

    # Usuário consulta os próprios chamados
    resp_lista = client.get(
        '/api/support/tickets/mine',
        headers=non_admin_auth_headers,
    )
    assert resp_lista.status_code == 200
    itens = resp_lista.get_json()
    assert any(item['id'] == ticket['id'] for item in itens)


def test_admin_lista_atualiza_e_obtem_indicadores(
    client, suporte_dados_iniciais, non_admin_auth_headers, login_admin
):
    dados = suporte_dados_iniciais
    csrf_token = dados['csrf_token']

    # Cria um chamado para existir nos relatórios
    response = client.post(
        '/api/support/tickets',
        data={
            'areaId': str(dados['area_id']),
            'equipamentoId': str(dados['equipamento_id']),
            'descricao': 'Impressora com atolamento de papel constante.',
            'urgencia': 'media',
        },
        headers=_headers_with_csrf(non_admin_auth_headers, csrf_token),
        content_type='multipart/form-data',
    )
    assert response.status_code == 201
    ticket_id = response.get_json()['id']

    token_admin, _ = login_admin(client)
    admin_headers = {'Authorization': f'Bearer {token_admin}', 'X-CSRF-Token': csrf_token}

    resp_admin_lista = client.get('/api/support/tickets', headers=admin_headers)
    assert resp_admin_lista.status_code == 200
    dados_lista = resp_admin_lista.get_json()
    assert dados_lista['total'] >= 1
    assert any(item['id'] == ticket_id for item in dados_lista['items'])

    resp_update = client.patch(
        f'/api/support/tickets/{ticket_id}',
        json={'status': 'resolvido', 'urgencia': 'alta'},
        headers=admin_headers,
    )
    assert resp_update.status_code == 200
    ticket_atualizado = resp_update.get_json()
    assert ticket_atualizado['status'] == 'resolvido'
    assert ticket_atualizado['resolvido_em'] is not None

    resp_indicadores = client.get('/api/support/indicadores', headers=admin_headers)
    assert resp_indicadores.status_code == 200
    indicadores = resp_indicadores.get_json()
    assert 'total_chamados' in indicadores
    assert 'chamados_por_status' in indicadores
    assert indicadores['chamados_por_status']['resolvido'] >= 1


def test_base_conhecimento_crud(client, suporte_dados_iniciais, login_admin):
    dados = suporte_dados_iniciais
    csrf_token = dados['csrf_token']
    token_admin, _ = login_admin(client)
    admin_headers = {'Authorization': f'Bearer {token_admin}', 'X-CSRF-Token': csrf_token}

    resp_create = client.post(
        '/api/support/areas',
        json={'nome': 'Suporte Redes', 'descricao': 'Infraestrutura de redes', 'ativo': True},
        headers=admin_headers,
    )
    assert resp_create.status_code == 201
    area_id = resp_create.get_json()['id']

    resp_update = client.put(
        f'/api/support/areas/{area_id}',
        json={'nome': 'Suporte de Redes', 'descricao': 'Equipe de redes', 'ativo': False},
        headers=admin_headers,
    )
    assert resp_update.status_code == 200
    area_json = resp_update.get_json()
    assert area_json['nome'] == 'Suporte de Redes'
    assert area_json['ativo'] is False

    resp_delete = client.delete(f'/api/support/areas/{area_id}', headers=admin_headers)
    assert resp_delete.status_code == 204

    # Equipamentos CRUD
    resp_create_eq = client.post(
        '/api/support/equipamentos',
        json={'nome': 'Desktop', 'descricao': 'Computador de mesa', 'ativo': True},
        headers=admin_headers,
    )
    assert resp_create_eq.status_code == 201
    equipamento_id = resp_create_eq.get_json()['id']

    resp_update_eq = client.put(
        f'/api/support/equipamentos/{equipamento_id}',
        json={'nome': 'Desktop', 'descricao': 'Atualizado', 'ativo': True},
        headers=admin_headers,
    )
    assert resp_update_eq.status_code == 200
    assert resp_update_eq.get_json()['descricao'] == 'Atualizado'

    resp_delete_eq = client.delete(
        f'/api/support/equipamentos/{equipamento_id}', headers=admin_headers
    )
    assert resp_delete_eq.status_code == 204
