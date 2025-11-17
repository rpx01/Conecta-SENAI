"""Blueprints do módulo de suporte de TI."""
from .publico import (  # noqa: F401
    suporte_ti_public_bp,
    suporte_ti_public_html_bp,
)
from .admin import suporte_ti_admin_bp  # noqa: F401

__all__ = [
    "suporte_ti_public_bp",
    "suporte_ti_public_html_bp",
    "suporte_ti_admin_bp",
]
