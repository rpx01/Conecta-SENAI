import pytest
from sqlalchemy import text
from src.models import db


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


@pytest.mark.usefixtures("app")
def test_listar_horarios_sem_coluna_turno(client, app):
    """Garante que a listagem não falha sem a coluna 'turno'."""
    with app.app_context():
        db.session.execute(text("ALTER TABLE planejamento_horarios DROP COLUMN turno"))
        db.session.commit()

    resp = client.get("/api/horarios")
    assert resp.status_code == 200
    data = resp.get_json()
    assert all(h.get("turno") is None for h in data)


@pytest.mark.usefixtures("app")
def test_criar_horario_sem_coluna_turno(client, app):
    """Mesmo sem a coluna 'turno', o cadastro deve funcionar."""
    with app.app_context():
        db.session.execute(text("ALTER TABLE planejamento_horarios DROP COLUMN turno"))
        db.session.commit()

    resp = client.post(
        "/api/horarios",
        json={"nome": "Horario X", "turno": "manhã"},
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["nome"] == "Horario X"
    assert data["turno"] is None


@pytest.mark.usefixtures("app")
def test_atualizar_horario_sem_coluna_turno(client, app):
    """Atualização deve ocorrer mesmo sem a coluna 'turno'."""
    with app.app_context():
        db.session.execute(text("ALTER TABLE planejamento_horarios DROP COLUMN turno"))
        db.session.commit()

    resp = client.post(
        "/api/horarios",
        json={"nome": "Horario Y", "turno": "manhã"},
    )
    horario_id = resp.get_json()["id"]

    resp = client.put(
        f"/api/horarios/{horario_id}",
        json={"nome": "Horario Z", "turno": "tarde"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["nome"] == "Horario Z"
    assert data["turno"] is None


@pytest.mark.usefixtures("app")
def test_excluir_horario_sem_coluna_turno(client, app):
    """Exclusão não deve falhar se a coluna 'turno' não existir."""
    with app.app_context():
        db.session.execute(text("ALTER TABLE planejamento_horarios DROP COLUMN turno"))
        db.session.commit()

    resp = client.post(
        "/api/horarios",
        json={"nome": "Horario W", "turno": "manhã"},
    )
    horario_id = resp.get_json()["id"]

    resp = client.delete(f"/api/horarios/{horario_id}")
    assert resp.status_code == 200
    resp = client.get("/api/horarios")
    assert all(h["id"] != horario_id for h in resp.get_json())
