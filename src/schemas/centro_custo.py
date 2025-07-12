from pydantic import BaseModel, Field
from typing import Optional

class CentroCustoCreateSchema(BaseModel):
    nome: str
    descricao: Optional[str] = None
    ativo: Optional[bool] = True

class CentroCustoUpdateSchema(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    ativo: Optional[bool] = None
