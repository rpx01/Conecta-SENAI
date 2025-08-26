from typing import Literal, Optional
from pydantic import BaseModel

TurnoLiteral = Literal[
    'manhã',
    'tarde',
    'noite',
    'manhã/tarde',
    'tarde/noite',
]


class HorarioBase(BaseModel):
    nome: str


class HorarioCreate(HorarioBase):
    turno: TurnoLiteral


class HorarioUpdate(BaseModel):
    nome: Optional[str] = None
    turno: Optional[TurnoLiteral] = None


class HorarioRead(HorarioBase):
    id: int
    turno: Optional[TurnoLiteral] = None

    class Config:
        orm_mode = True
