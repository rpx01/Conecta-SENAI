from pydantic import BaseModel, Field
from typing import Optional

class OcupacaoCreateSchema(BaseModel):
    sala_id: int
    curso_evento: str
    data_inicio: str
    data_fim: str
    turno: str
    instrutor_id: Optional[int] = None
    tipo_ocupacao: Optional[str] = 'aula_regular'
    recorrencia: Optional[str] = 'unica'
    status: Optional[str] = 'confirmado'
    observacoes: Optional[str] = None

class OcupacaoUpdateSchema(BaseModel):
    sala_id: Optional[int] = None
    instrutor_id: Optional[int] = None
    curso_evento: Optional[str] = None
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    data: Optional[str] = None
    turno: Optional[str] = None
    horario_inicio: Optional[str] = None
    horario_fim: Optional[str] = None
    tipo_ocupacao: Optional[str] = None
    recorrencia: Optional[str] = None
    status: Optional[str] = None
    observacoes: Optional[str] = None
