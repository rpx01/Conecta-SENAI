"""Serviços para gerenciamento de horários."""

from src.models import db, Horario, TurnoEnum


def create_horario(data: dict) -> Horario:
    turno = data.get("turno")
    horario = Horario(
        nome=data["nome"].strip(),
        turno=TurnoEnum(turno) if turno else None,
    )
    db.session.add(horario)
    db.session.commit()
    return horario


def update_horario(horario: Horario, data: dict) -> Horario:
    if data.get("nome") is not None:
        horario.nome = data["nome"].strip()
    if "turno" in data:
        turno = data.get("turno")
        horario.turno = TurnoEnum(turno) if turno else None
    db.session.commit()
    return horario
