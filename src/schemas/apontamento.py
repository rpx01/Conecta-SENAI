from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class ApontamentoCreateSchema(BaseModel):
    data: date
    horas: float = Field(gt=0)
    descricao: Optional[str] = None
    status: Optional[str] = 'pendente'
    instrutor_id: int
    centro_custo_id: int
    ocupacao_id: Optional[int] = None

class ApontamentoUpdateSchema(BaseModel):
    data: Optional[date] = None
    horas: Optional[float] = Field(default=None, gt=0)
    descricao: Optional[str] = None
    status: Optional[str] = None
    instrutor_id: Optional[int] = None
    centro_custo_id: Optional[int] = None
    ocupacao_id: Optional[int] = None
