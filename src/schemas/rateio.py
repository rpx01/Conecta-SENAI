from pydantic import BaseModel, Field
from typing import Optional


class RateioParametroCreateSchema(BaseModel):
    filial: str
    uo: str
    cr: str
    classe_valor: str


class RateioParametroUpdateSchema(BaseModel):
    filial: Optional[str] = None
    uo: Optional[str] = None
    cr: Optional[str] = None
    classe_valor: Optional[str] = None


class RateioLancamentoCreateSchema(BaseModel):
    instrutor_id: int
    parametro_id: int
    data_referencia: str
    valor_total: float
    horas_trabalhadas: float
    observacoes: Optional[str] = None


class RateioLancamentoUpdateSchema(BaseModel):
    parametro_id: Optional[int] = None
    data_referencia: Optional[str] = None
    valor_total: Optional[float] = None
    horas_trabalhadas: Optional[float] = None
    observacoes: Optional[str] = None
