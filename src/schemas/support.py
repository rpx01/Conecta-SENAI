"""Esquemas de validação para o módulo de suporte de TI."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.utils.support_constants import VALID_STATUSES, VALID_URGENCIAS


class SupportTicketCreateSchema(BaseModel):
    """Dados necessários para abertura de um novo chamado."""

    nome: str = Field(min_length=2, max_length=150)
    email: EmailStr
    area_id: int | None = Field(default=None, alias="areaId")
    equipamento_id: int | None = Field(default=None, alias="equipamentoId")
    patrimonio: str | None = Field(default=None, max_length=100)
    numero_serie: str | None = Field(default=None, alias="numeroSerie", max_length=100)
    descricao: str = Field(min_length=10)
    urgencia: str = Field(alias="urgencia")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @field_validator("urgencia")
    @classmethod
    def validar_urgencia(cls, valor: str) -> str:
        normalizado = (valor or "").strip().lower()
        if normalizado not in VALID_URGENCIAS:
            raise ValueError(
                "Urgência inválida. Valores aceitos: " + ", ".join(VALID_URGENCIAS)
            )
        return normalizado

    @field_validator("nome", "descricao", "patrimonio", "numero_serie")
    @classmethod
    def limpar_texto(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        texto = valor.strip()
        return texto or None


class SupportTicketUpdateSchema(BaseModel):
    """Dados aceitos ao atualizar um chamado."""

    status: str | None = None
    urgencia: str | None = None
    area_id: int | None = Field(default=None, alias="areaId")
    equipamento_id: int | None = Field(default=None, alias="equipamentoId")
    patrimonio: str | None = Field(default=None, max_length=100)
    numero_serie: str | None = Field(default=None, alias="numeroSerie", max_length=100)
    descricao: str | None = None

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @field_validator("status")
    @classmethod
    def validar_status(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        normalizado = valor.strip().lower()
        if normalizado not in VALID_STATUSES:
            raise ValueError(
                "Status inválido. Valores aceitos: " + ", ".join(VALID_STATUSES)
            )
        return normalizado

    @field_validator("urgencia")
    @classmethod
    def validar_urgencia(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        normalizado = valor.strip().lower()
        if normalizado not in VALID_URGENCIAS:
            raise ValueError(
                "Urgência inválida. Valores aceitos: " + ", ".join(VALID_URGENCIAS)
            )
        return normalizado

    @field_validator("descricao", "patrimonio", "numero_serie")
    @classmethod
    def limpar_texto(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        texto = valor.strip()
        return texto or None


class SupportKnowledgeBaseSchema(BaseModel):
    """Schema genérico para cadastro de dados auxiliares."""

    nome: str = Field(min_length=2, max_length=120)
    descricao: str | None = Field(default=None, max_length=255)
    ativo: bool = Field(default=True)

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @field_validator("nome", "descricao")
    @classmethod
    def limpar_texto(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        texto = valor.strip()
        return texto or None
