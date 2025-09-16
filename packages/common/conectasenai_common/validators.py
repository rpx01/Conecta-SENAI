"""Validações e expressões reutilizáveis."""
from __future__ import annotations

import re

PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")


def is_strong_password(value: str) -> bool:
    """Retorna ``True`` se a senha atender aos requisitos mínimos."""
    return bool(PASSWORD_REGEX.match(value))


__all__ = ["PASSWORD_REGEX", "is_strong_password"]
