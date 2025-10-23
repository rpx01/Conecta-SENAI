"""Blueprints do módulo de suporte de TI."""
from .publico import suporte_ti_public_bp  # noqa: F401
from .admin import suporte_ti_admin_bp  # noqa: F401

__all__ = [
    "suporte_ti_public_bp",
    "suporte_ti_admin_bp",
]
