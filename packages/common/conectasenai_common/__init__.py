"""Pacote com utilitários compartilhados do Conecta-SENAI."""

from .email import (
    Address,
    RateLimiter,
    build_turma_context,
    build_user_context,
    normalize_addresses,
    parse_time,
)

__all__ = [
    "Address",
    "RateLimiter",
    "build_turma_context",
    "build_user_context",
    "normalize_addresses",
    "parse_time",
]
