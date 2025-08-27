import pytest


@pytest.mark.usefixtures("app")
def test_criar_e_atualizar_horario_basedados(client):
    # Cria novo horário
    resp = client.post(
        "/api/horario",
        json={"nome": "08:00 as 10:00", "turno": "manha"},
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["turno"] == "manha"
    horario_id = data["id"]

    # Atualiza o turno do horário
    resp = client.put(
        f"/api/horario/{horario_id}",
        json={"nome": "08:00 as 10:00", "turno": "tarde"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["turno"] == "tarde"

    # Confirma persistência
    resp = client.get("/api/horario")
    assert resp.status_code == 200
    itens = resp.get_json()
    assert any(h["id"] == horario_id and h["turno"] == "tarde" for h in itens)
