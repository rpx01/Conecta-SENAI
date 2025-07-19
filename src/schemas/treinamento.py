from pydantic import BaseModel, Field
from typing import List, Optional

class MaterialDidaticoSchema(BaseModel):
    descricao: Optional[str] = 'Material Principal'
    url: str

class TreinamentoCreateSchema(BaseModel):
    nome: str
    codigo: Optional[str] = None
    carga_horaria: int = Field(gt=0)
    materiais: Optional[List[MaterialDidaticoSchema]] = None
