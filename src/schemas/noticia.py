"""Esquemas de validação para o módulo de notícias."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _parse_datetime(value: Optional[str | datetime]) -> Optional[datetime]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    try:
        str_value = str(value).strip()
        if str_value.endswith("Z"):
            str_value = f"{str_value[:-1]}+00:00"
        return datetime.fromisoformat(str_value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - validação explícita
        raise ValueError("Data de publicação inválida. Use o formato ISO 8601.") from exc


class NoticiaBaseSchema(BaseModel):
    titulo: str = Field(min_length=3, max_length=200)
    resumo: str = Field(min_length=10, max_length=400)
    conteudo: str = Field(min_length=20)
    autor: Optional[str] = Field(default=None, max_length=120)
    imagem_url: Optional[str] = Field(default=None, max_length=500)
    destaque: bool = False
    ativo: bool = True
    data_publicacao: Optional[datetime] = Field(default=None, alias="dataPublicacao")

    @field_validator("titulo", "resumo", "conteudo", "autor", "imagem_url", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Optional[str]):
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned
        return value

    @field_validator("data_publicacao", mode="before")
    @classmethod
    def validar_data_publicacao(cls, value):
        return _parse_datetime(value)

    class Config:
        populate_by_name = True


class NoticiaCreateSchema(NoticiaBaseSchema):
    pass


class NoticiaUpdateSchema(BaseModel):
    titulo: Optional[str] = Field(default=None, min_length=3, max_length=200)
    resumo: Optional[str] = Field(default=None, min_length=10, max_length=400)
    conteudo: Optional[str] = Field(default=None, min_length=20)
    autor: Optional[str] = Field(default=None, max_length=120)
    imagem_url: Optional[str] = Field(default=None, max_length=500)
    destaque: Optional[bool] = None
    ativo: Optional[bool] = None
    data_publicacao: Optional[datetime] = Field(default=None, alias="dataPublicacao")

    @field_validator("titulo", "resumo", "conteudo", "autor", "imagem_url", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Optional[str]):
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned
        return value

    @field_validator("data_publicacao", mode="before")
    @classmethod
    def validar_data_publicacao(cls, value):
        return _parse_datetime(value)

    class Config:
        populate_by_name = True
