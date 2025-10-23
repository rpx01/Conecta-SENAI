"""Esquemas Pydantic para o recurso de horários."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


TurnoLiteral = Literal["Manhã", "Tarde", "Noite", "Manhã/Tarde", "Tarde/Noite"]


class HorarioIn(BaseModel):
    nome: str
    turno: Optional[TurnoLiteral] = None


class HorarioOut(BaseModel):
    id: int
    nome: str
    turno: Optional[TurnoLiteral] = None

    model_config = ConfigDict(from_attributes=True)
