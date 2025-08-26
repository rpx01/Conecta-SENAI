from typing import Literal
from pydantic import BaseModel, ConfigDict, constr

TurnoLiteral = Literal["manhã", "tarde", "noite", "manhã/tarde", "tarde/noite"]


class HorarioCreateSchema(BaseModel):
    nome: constr(min_length=1, strip_whitespace=True)
    turno: TurnoLiteral
    model_config = ConfigDict(from_attributes=True)


class HorarioOutSchema(HorarioCreateSchema):
    id: int
