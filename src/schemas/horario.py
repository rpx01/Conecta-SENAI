"""Schemas para o modelo Horario."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, constr


class TurnoEnum(str, Enum):
    MANHA = "MANHA"
    TARDE = "TARDE"
    NOITE = "NOITE"
    MANHA_TARDE = "MANHA_TARDE"
    TARDE_NOITE = "TARDE_NOITE"


class HorarioCreate(BaseModel):
    nome: constr(min_length=1, strip_whitespace=True)
    turno: Optional[TurnoEnum] = None
    model_config = ConfigDict(from_attributes=True)


class HorarioUpdate(BaseModel):
    nome: Optional[constr(min_length=1, strip_whitespace=True)] = None
    turno: Optional[TurnoEnum] = None
    model_config = ConfigDict(from_attributes=True)


class HorarioOut(BaseModel):
    id: int
    nome: str
    turno: Optional[TurnoEnum] = None
    model_config = ConfigDict(from_attributes=True)
