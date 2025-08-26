"""Rotas para gerenciamento de horários."""

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError, OperationalError
from sqlalchemy import text
from pydantic import ValidationError

from src.models import db, Horario
from src.schemas.horario import HorarioCreateSchema, HorarioOutSchema
from src.services.horario_service import create_horario, update_horario
from src.utils.error_handler import handle_internal_error

horario_bp = Blueprint("horario", __name__)


@horario_bp.route("/horarios", methods=["GET"])
def listar_horarios():
    """Lista horários, lidando com ausência da coluna 'turno'."""
    try:
        horarios = Horario.query.order_by(Horario.nome).all()
        payload = [
            {"id": h.id, "nome": h.nome, "turno": getattr(h, "turno", None)}
            for h in horarios
        ]
    except (ProgrammingError, OperationalError):  # coluna 'turno' ausente
        db.session.rollback()
        result = db.session.execute(
            text("SELECT id, nome FROM planejamento_horarios ORDER BY nome")
        )
        payload = [{"id": row.id, "nome": row.nome, "turno": None} for row in result]
    return jsonify(payload)


@horario_bp.route("/horarios", methods=["POST"])
def criar_horario():
    data = request.get_json(silent=True) or {}
    try:
        validated = HorarioCreateSchema(**data)
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400
    try:
        exists = Horario.query.filter_by(nome=validated.nome).first()
    except (ProgrammingError, OperationalError):
        db.session.rollback()
        exists = db.session.execute(
            text(
                "SELECT 1 FROM planejamento_horarios WHERE nome=:nome LIMIT 1"
            ),
            {"nome": validated.nome},
        ).first()
    if exists:
        return jsonify({"erro": "Já existe um horário com este nome"}), 400
    try:
        horario = create_horario(validated.model_dump())
        out = HorarioOutSchema(
            id=horario.id, nome=horario.nome, turno=horario.turno
        )
        return jsonify(out.model_dump()), 201
    except (ProgrammingError, OperationalError):
        db.session.rollback()
        result = db.session.execute(
            text(
                "INSERT INTO planejamento_horarios (nome) VALUES (:nome) RETURNING id, nome"
            ),
            {"nome": validated.nome},
        ).mappings().first()
        db.session.commit()
        out = HorarioOutSchema(id=result["id"], nome=result["nome"], turno=None)
        return jsonify(out.model_dump()), 201
    except SQLAlchemyError as e:  # pragma: no cover - segurança
        db.session.rollback()
        return handle_internal_error(e)


@horario_bp.route("/horarios/<int:horario_id>", methods=["PUT", "PATCH"])
def atualizar_horario(horario_id: int):
    try:
        horario = db.session.get(Horario, horario_id)
        coluna_turno = True
    except (ProgrammingError, OperationalError):
        db.session.rollback()
        horario = None
        coluna_turno = False

    data = request.get_json(silent=True) or {}

    if not coluna_turno:
        result = db.session.execute(
            text(
                "SELECT id, nome FROM planejamento_horarios WHERE id=:id"
            ),
            {"id": horario_id},
        ).mappings().first()
        if not result:
            return jsonify({"erro": "Horário não encontrado"}), 404
        payload = {
            "nome": data.get("nome", result["nome"]),
            "turno": data.get("turno", "manhã"),
        }
        try:
            validated = HorarioCreateSchema(**payload)
        except ValidationError as e:
            return jsonify({"erro": e.errors()}), 400
        if db.session.execute(
            text(
                "SELECT 1 FROM planejamento_horarios WHERE nome=:nome AND id<>:id LIMIT 1"
            ),
            {"nome": validated.nome, "id": horario_id},
        ).first():
            return jsonify({"erro": "Já existe um horário com este nome"}), 400
        db.session.execute(
            text(
                "UPDATE planejamento_horarios SET nome=:nome WHERE id=:id"
            ),
            {"nome": validated.nome, "id": horario_id},
        )
        db.session.commit()
        out = HorarioOutSchema(id=horario_id, nome=validated.nome, turno=None)
        return jsonify(out.model_dump())

    if not horario:
        return jsonify({"erro": "Horário não encontrado"}), 404
    payload = {
        "nome": data.get("nome", horario.nome),
        "turno": data.get("turno", horario.turno),
    }
    try:
        validated = HorarioCreateSchema(**payload)
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400
    if (
        validated.nome != horario.nome
        and Horario.query.filter_by(nome=validated.nome).first()
    ):
        return jsonify({"erro": "Já existe um horário com este nome"}), 400
    try:
        horario = update_horario(horario, validated.model_dump())
        out = HorarioOutSchema(
            id=horario.id, nome=horario.nome, turno=horario.turno
        )
        return jsonify(out.model_dump())
    except (ProgrammingError, OperationalError):
        db.session.rollback()
        db.session.execute(
            text(
                "UPDATE planejamento_horarios SET nome=:nome WHERE id=:id"
            ),
            {"nome": validated.nome, "id": horario_id},
        )
        db.session.commit()
        out = HorarioOutSchema(id=horario_id, nome=validated.nome, turno=None)
        return jsonify(out.model_dump())
    except SQLAlchemyError as e:  # pragma: no cover - segurança
        db.session.rollback()
        return handle_internal_error(e)


@horario_bp.route("/horarios/<int:horario_id>", methods=["DELETE"])
def excluir_horario(horario_id: int):
    try:
        horario = db.session.get(Horario, horario_id)
        coluna_turno = True
    except (ProgrammingError, OperationalError):
        db.session.rollback()
        coluna_turno = False

    if not coluna_turno:
        result = db.session.execute(
            text(
                "DELETE FROM planejamento_horarios WHERE id=:id RETURNING id"
            ),
            {"id": horario_id},
        ).first()
        if not result:
            return jsonify({"erro": "Horário não encontrado"}), 404
        db.session.commit()
        return jsonify({"mensagem": "Horário excluído com sucesso"}), 200

    if not horario:
        return jsonify({"erro": "Horário não encontrado"}), 404
    db.session.delete(horario)
    db.session.commit()
    return jsonify({"mensagem": "Horário excluído com sucesso"}), 200
