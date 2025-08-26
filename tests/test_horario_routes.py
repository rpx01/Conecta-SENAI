import pytest


@pytest.mark.usefixtures("app")
def test_criar_horario_valido(client):
    resp = client.post(
        "/api/horarios",
        json={"nome": "Horario Manha", "turno": "manhã"},
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["nome"] == "Horario Manha"
    assert data["turno"] == "manhã"
    assert "id" in data


@pytest.mark.usefixtures("app")
def test_criar_horario_turno_invalido(client):
    resp = client.post(
        "/api/horarios",
        json={"nome": "Horario X", "turno": "invalido"},
    )
    assert resp.status_code == 400


@pytest.mark.usefixtures("app")
def test_listar_horarios_retorna_turno(client):
    client.post(
        "/api/horarios",
        json={"nome": "Horario Tarde", "turno": "tarde"},
    )
    resp = client.get("/api/horarios")
    assert resp.status_code == 200
    data = resp.get_json()
    assert any(h["nome"] == "Horario Tarde" and h["turno"] == "tarde" for h in data)
