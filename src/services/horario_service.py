"""Serviços para gerenciamento de horários."""

from src.models import db, Horario
from src.schemas.horario import HorarioCreate, HorarioUpdate


def create_horario(data: HorarioCreate) -> Horario:
    horario = Horario(nome=data.nome, turno=data.turno)
    db.session.add(horario)
    db.session.commit()
    return horario


def update_horario(horario: Horario, data: HorarioUpdate) -> Horario:
    if data.nome is not None:
        horario.nome = data.nome
    if data.turno is not None:
        horario.turno = data.turno
    db.session.commit()
    return horario
