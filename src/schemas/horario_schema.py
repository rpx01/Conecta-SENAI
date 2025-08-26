from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, constr

TurnoLiteral = Literal["Manhã", "Tarde", "Noite", "Manhã/Tarde", "Tarde/Noite"]


class HorarioBase(BaseModel):
    nome: constr(min_length=1, strip_whitespace=True)
    turno: Optional[TurnoLiteral] = None
    model_config = ConfigDict(from_attributes=True)


class HorarioCreate(HorarioBase):
    pass


class HorarioUpdate(BaseModel):
    nome: Optional[constr(min_length=1, strip_whitespace=True)] = None
    turno: Optional[TurnoLiteral] = None
    model_config = ConfigDict(from_attributes=True)


class HorarioOut(HorarioBase):
    id: int
