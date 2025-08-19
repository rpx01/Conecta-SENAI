from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError, field_validator


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
