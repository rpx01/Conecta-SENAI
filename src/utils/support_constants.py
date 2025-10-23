"""Constantes compartilhadas para o módulo de Suporte de TI."""

from __future__ import annotations

from dataclasses import dataclass


VALID_URGENCIAS: tuple[str, ...] = ("baixa", "media", "alta", "critica")
VALID_STATUSES: tuple[str, ...] = ("aberto", "em_andamento", "resolvido", "encerrado")


@dataclass(frozen=True)
class SupportLookupItem:
    """Representa um item retornado para o frontend."""

    id: int
    nome: str
    descricao: str | None = None
    ativo: bool = True
