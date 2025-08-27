from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict, constr
from enum import Enum


class PolosSchema(BaseModel):
    cmd: bool = False
    sjb: bool = False
    sag_tombos: bool = Field(False, alias="sag_tombos")


class RegistroPlanejamentoSchema(BaseModel):
    inicio: date
    fim: date
    semana: Optional[str] = None
    horario: str
    carga_horaria: int = Field(..., alias="carga_horaria")
    modalidade: Optional[str] = None
    treinamento: str
    polos: PolosSchema
    instrutor: str
    local: Optional[str] = ""
    observacao: Optional[str] = ""
    sge_ativo: bool = False
    sge_link: Optional[str] = None

    @field_validator("fim")
    @classmethod
    def validar_fim(cls, v, info):
        inicio = info.data.get("inicio")
        if inicio and v < inicio:
            raise ValueError("Data final anterior à inicial")
        return v

    @field_validator("horario")
    @classmethod
    def validar_horario(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
        except Exception as exc:  # noqa: PIE-786
            raise ValueError("Formato de horário inválido, use HH:MM") from exc
        return v

    @field_validator("carga_horaria")
    @classmethod
    def validar_carga(cls, v):
        if v <= 0:
            raise ValueError("Carga horária deve ser maior que zero")
        return v


class PlanejamentoCreateSchema(BaseModel):
    registros: List[RegistroPlanejamentoSchema]

    class Config:
        populate_by_name = True


class TurnoEnum(str, Enum):
    MANHA = "manha"
    TARDE = "tarde"
    NOITE = "noite"
    MANHA_TARDE = "manha_tarde"
    TARDE_NOITE = "tarde_noite"


class HorarioBase(BaseModel):
    nome: constr(min_length=1, strip_whitespace=True)
    turno: TurnoEnum
    model_config = ConfigDict(from_attributes=True)


class HorarioCreate(HorarioBase):
    pass


class HorarioUpdate(BaseModel):
    nome: Optional[constr(min_length=1, strip_whitespace=True)] = None
    turno: Optional[TurnoEnum] = None
    model_config = ConfigDict(from_attributes=True)


class HorarioOut(HorarioBase):
    id: int
