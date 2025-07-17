from pydantic import BaseModel
from typing import Optional, List


class MaterialSchema(BaseModel):
    descricao: str
    url: str


class TreinamentoCreateSchema(BaseModel):
    nome: str
    codigo: Optional[str] = None
    carga_horaria: int
    materiais: Optional[List[MaterialSchema]] = []


class TurmaCreateSchema(BaseModel):
    treinamento_id: int
    data_inicio: str
    data_fim: str
    status: Optional[str] = 'A realizar'
    instrutor_ids: List[int]


class InscricaoSchema(BaseModel):
    turma_id: int
    usuario_id: int
