"""Rotas para gerenciamento de horários."""

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import (
    SQLAlchemyError,
    ProgrammingError,
    OperationalError,
    IntegrityError,
)
from sqlalchemy import text
from pydantic import ValidationError
from enum import Enum as PyEnum

from src.models import db, Horario
from src.schemas.planejamento import HorarioCreate, HorarioUpdate, HorarioOut
from src.utils.error_handler import handle_internal_error

horario_bp = Blueprint("horario", __name__)


# Mapas para compatibilizar valores antigos de turno no banco
LEGACY_FORMS = {
    "manha": ["Manhã", "manhã"],
    "tarde": ["Tarde", "tarde"],
    "noite": ["Noite", "noite"],
    "manha_tarde": ["Manhã/Tarde", "manhã/tarde"],
    "tarde_noite": ["Tarde/Noite", "tarde/noite"],
}
LEGACY_TO_CANON = {
    legacy: canon for canon, forms in LEGACY_FORMS.items() for legacy in forms
}
CANON_TO_LEGACY = {canon: forms[0] for canon, forms in LEGACY_FORMS.items()}


def _to_canonical(turno):
    """Converte valores de turno legados para o formato canônico."""
    if isinstance(turno, PyEnum):
        turno = turno.value
    return LEGACY_TO_CANON.get(turno, turno)


def _legacy_variants(turno):
    """Retorna possíveis representações legadas para um turno canônico."""
    if isinstance(turno, PyEnum):
        turno = turno.value
    return LEGACY_FORMS.get(turno, [turno])


def _to_legacy(turno):
    """Converte turno canônico para uma forma legada padrão."""
    if isinstance(turno, PyEnum):
        turno = turno.value
    return CANON_TO_LEGACY.get(turno, turno)


@horario_bp.route("/horarios", methods=["GET"])
def listar_horarios():
    """Lista horários, lidando com ausência da coluna 'turno'."""
    try:
        horarios = Horario.query.order_by(Horario.nome).all()
        payload = []
        for h in horarios:
            turno = _to_canonical(getattr(h, "turno", None))
            payload.append({"id": h.id, "nome": h.nome, "turno": turno})
    except (
        ProgrammingError,
        OperationalError,
        IntegrityError,
        ValueError,
        LookupError,
    ):
        db.session.rollback()
        try:
            result = db.session.execute(
                text("SELECT id, nome, turno FROM planejamento_horarios ORDER BY nome")
            )
            payload = []
            for row in result.mappings():
                turno = _to_canonical(row.get("turno"))
                payload.append({"id": row["id"], "nome": row["nome"], "turno": turno})
        except (ProgrammingError, OperationalError, IntegrityError):
            db.session.rollback()
            result = db.session.execute(
                text("SELECT id, nome FROM planejamento_horarios ORDER BY nome")
            )
            payload = [
                {"id": row.id, "nome": row.nome, "turno": None} for row in result
            ]
    return jsonify(payload)


@horario_bp.route("/horarios", methods=["POST"])
def criar_horario():
    data = request.get_json(silent=True) or {}
    try:
        validated = HorarioCreate(**data)
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400
    try:
        exists = Horario.query.filter_by(nome=validated.nome).first()
    except (ProgrammingError, OperationalError, IntegrityError):
        db.session.rollback()
        exists = db.session.execute(
            text("SELECT 1 FROM planejamento_horarios WHERE nome=:nome LIMIT 1"),
            {"nome": validated.nome},
        ).first()
    if exists:
        return jsonify({"erro": "Já existe um horário com este nome"}), 400
    try:
        horario = Horario(nome=validated.nome, turno=validated.turno)
        db.session.add(horario)
        db.session.commit()
        out = HorarioOut(
            id=horario.id, nome=horario.nome, turno=_to_canonical(horario.turno)
        )
        return jsonify(out.model_dump()), 201
    except (
        ProgrammingError,
        OperationalError,
        IntegrityError,
        ValueError,
        LookupError,
    ):
        db.session.rollback()
        # Tenta inserir diretamente com o valor canônico
        try:
            result = (
                db.session.execute(
                    text(
                        "INSERT INTO planejamento_horarios (nome, turno) VALUES (:nome, :turno) RETURNING id, nome, turno"
                    ),
                    {"nome": validated.nome, "turno": validated.turno.value},
                )
                .mappings()
                .first()
            )
            db.session.commit()
        except (ProgrammingError, OperationalError, IntegrityError):
            db.session.rollback()
            result = None
            for legacy_turno in _legacy_variants(validated.turno):
                try:
                    result = (
                        db.session.execute(
                            text(
                                "INSERT INTO planejamento_horarios (nome, turno) VALUES (:nome, :turno) RETURNING id, nome, turno"
                            ),
                            {"nome": validated.nome, "turno": legacy_turno},
                        )
                        .mappings()
                        .first()
                    )
                    db.session.commit()
                    break
                except (ProgrammingError, OperationalError, IntegrityError):
                    db.session.rollback()
            if result is None:
                result = (
                    db.session.execute(
                        text(
                            "INSERT INTO planejamento_horarios (nome) VALUES (:nome) RETURNING id, nome"
                        ),
                        {"nome": validated.nome},
                    )
                    .mappings()
                    .first()
                )
                db.session.commit()
                turno = None
                out = {"id": result["id"], "nome": result["nome"], "turno": turno}
                return jsonify(out), 201
        turno = _to_canonical(result.get("turno"))
        out = {"id": result["id"], "nome": result["nome"], "turno": turno}
        return jsonify(out), 201
    except SQLAlchemyError as e:  # pragma: no cover - segurança
        db.session.rollback()
        return handle_internal_error(e)


@horario_bp.route("/horarios/<int:horario_id>", methods=["PUT", "PATCH"])
def atualizar_horario(horario_id: int):
    try:
        horario = db.session.get(Horario, horario_id)
        coluna_turno = True
    except (ProgrammingError, OperationalError, IntegrityError):
        db.session.rollback()
        horario = None
        coluna_turno = False

    data = request.get_json(silent=True) or {}
    try:
        validated = HorarioUpdate(**data)
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400

    if not coluna_turno:
        try:
            result = (
                db.session.execute(
                    text(
                        "SELECT id, nome, turno FROM planejamento_horarios WHERE id=:id"
                    ),
                    {"id": horario_id},
                )
                .mappings()
                .first()
            )
        except (ProgrammingError, OperationalError, IntegrityError):
            db.session.rollback()
            result = (
                db.session.execute(
                    text("SELECT id, nome FROM planejamento_horarios WHERE id=:id"),
                    {"id": horario_id},
                )
                .mappings()
                .first()
            )
            if not result:
                return jsonify({"erro": "Horário não encontrado"}), 404
            novo_nome = validated.nome if validated.nome is not None else result["nome"]
            if db.session.execute(
                text(
                    "SELECT 1 FROM planejamento_horarios WHERE nome=:nome AND id<>:id LIMIT 1"
                ),
                {"nome": novo_nome, "id": horario_id},
            ).first():
                return jsonify({"erro": "Já existe um horário com este nome"}), 400
            db.session.execute(
                text("UPDATE planejamento_horarios SET nome=:nome WHERE id=:id"),
                {"nome": novo_nome, "id": horario_id},
            )
            db.session.commit()
            out = {"id": horario_id, "nome": novo_nome, "turno": None}
            return jsonify(out)
        else:
            if not result:
                return jsonify({"erro": "Horário não encontrado"}), 404
            novo_nome = validated.nome if validated.nome is not None else result["nome"]
            turno_atual = _to_canonical(result.get("turno"))
            novo_turno = validated.turno if validated.turno is not None else turno_atual
            if db.session.execute(
                text(
                    "SELECT 1 FROM planejamento_horarios WHERE nome=:nome AND id<>:id LIMIT 1"
                ),
                {"nome": novo_nome, "id": horario_id},
            ).first():
                return jsonify({"erro": "Já existe um horário com este nome"}), 400
            try:
                db.session.execute(
                    text(
                        "UPDATE planejamento_horarios SET nome=:nome, turno=:turno WHERE id=:id"
                    ),
                    {
                        "nome": novo_nome,
                        "turno": getattr(novo_turno, "value", novo_turno),
                        "id": horario_id,
                    },
                )
                db.session.commit()
            except (ProgrammingError, OperationalError, IntegrityError):
                db.session.rollback()
                atualizado = False
                for legacy_turno in _legacy_variants(novo_turno):
                    try:
                        db.session.execute(
                            text(
                                "UPDATE planejamento_horarios SET nome=:nome, turno=:turno WHERE id=:id"
                            ),
                            {
                                "nome": novo_nome,
                                "turno": legacy_turno,
                                "id": horario_id,
                            },
                        )
                        db.session.commit()
                        atualizado = True
                        break
                    except (ProgrammingError, OperationalError, IntegrityError):
                        db.session.rollback()
                if not atualizado:
                    db.session.execute(
                        text(
                            "UPDATE planejamento_horarios SET nome=:nome WHERE id=:id"
                        ),
                        {"nome": novo_nome, "id": horario_id},
                    )
                    db.session.commit()
                    out = {"id": horario_id, "nome": novo_nome, "turno": None}
                    return jsonify(out)
            out = {
                "id": horario_id,
                "nome": novo_nome,
                "turno": _to_canonical(novo_turno),
            }
            return jsonify(out)

    if not horario:
        return jsonify({"erro": "Horário não encontrado"}), 404

    if (
        validated.nome is not None
        and validated.nome != horario.nome
        and Horario.query.filter_by(nome=validated.nome).first()
    ):
        return jsonify({"erro": "Já existe um horário com este nome"}), 400

    if validated.nome is not None:
        horario.nome = validated.nome
    if validated.turno is not None:
        horario.turno = validated.turno

    try:
        db.session.commit()
    except (ProgrammingError, OperationalError, IntegrityError):
        db.session.rollback()
        atualizado = False
        for legacy_turno in _legacy_variants(horario.turno):
            try:
                db.session.execute(
                    text(
                        "UPDATE planejamento_horarios SET nome=:nome, turno=:turno WHERE id=:id"
                    ),
                    {
                        "nome": horario.nome,
                        "turno": legacy_turno,
                        "id": horario_id,
                    },
                )
                db.session.commit()
                out = {
                    "id": horario_id,
                    "nome": horario.nome,
                    "turno": _to_canonical(legacy_turno),
                }
                atualizado = True
                return jsonify(out)
            except (ProgrammingError, OperationalError, IntegrityError):
                db.session.rollback()
        if not atualizado:
            db.session.execute(
                text("UPDATE planejamento_horarios SET nome=:nome WHERE id=:id"),
                {"nome": horario.nome, "id": horario_id},
            )
            db.session.commit()
            out = {"id": horario_id, "nome": horario.nome, "turno": None}
            return jsonify(out)
    except SQLAlchemyError as e:  # pragma: no cover - segurança
        db.session.rollback()
        return handle_internal_error(e)

    out = HorarioOut(
        id=horario.id, nome=horario.nome, turno=_to_canonical(horario.turno)
    )
    return jsonify(out.model_dump())


@horario_bp.route("/horarios/<int:horario_id>", methods=["DELETE"])
def excluir_horario(horario_id: int):
    try:
        horario = db.session.get(Horario, horario_id)
        coluna_turno = True
    except (ProgrammingError, OperationalError, IntegrityError):
        db.session.rollback()
        coluna_turno = False

    if not coluna_turno:
        result = db.session.execute(
            text("DELETE FROM planejamento_horarios WHERE id=:id RETURNING id"),
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
