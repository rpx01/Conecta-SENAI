from pydantic import BaseModel
from typing import Optional
from datetime import date


class InscricaoTreinamentoCreateSchema(BaseModel):
    nome: str
    email: str
    cpf: Optional[str] = None
    data_nascimento: Optional[date] = None
    empresa: Optional[str] = None
