"""Testes das rotas de horário."""
# flake8: noqa
import pytest


@pytest.mark.usefixtures("app")
def test_criar_horario_valido(client):
    resp = client.post(
        "/api/horarios",
        json={"nome": "Horario Manha", "turno": "MANHA"},
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["nome"] == "Horario Manha"
    assert data["turno"] == "MANHA"
    assert "id" in data


@pytest.mark.usefixtures("app")
def test_criar_horario_sem_turno(client):
    resp = client.post("/api/horarios", json={"nome": "Horario Livre"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["turno"] is None


@pytest.mark.usefixtures("app")
def test_criar_horario_turno_invalido(client):
    resp = client.post(
        "/api/horarios",
        json={"nome": "Horario X", "turno": "INEXISTENTE"},
    )
    assert resp.status_code == 400


@pytest.mark.usefixtures("app")
def test_listar_horarios_retorna_turno(client):
    client.post(
        "/api/horarios",
        json={"nome": "Horario Tarde", "turno": "TARDE"},
    )
    resp = client.get("/api/horarios")
    assert resp.status_code == 200
    data = resp.get_json()
    assert any(h["nome"] == "Horario Tarde" and h["turno"] == "TARDE" for h in data)


@pytest.mark.usefixtures("app")
def test_atualizar_horario(client):
    resp = client.post(
        "/api/horarios",
        json={"nome": "Horario X", "turno": "MANHA"},
    )
    horario_id = resp.get_json()["id"]

    resp = client.put(
        f"/api/horarios/{horario_id}",
        json={"nome": "Horario Z", "turno": "TARDE"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["nome"] == "Horario Z"
    assert data["turno"] == "TARDE"
