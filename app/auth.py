"""Utilitários de autenticação e autorização simples para o exemplo."""
from functools import wraps
from flask import g, request, abort

ROLE_ADMIN = "ROLE_ADMIN"
ROLE_GESTOR = "ROLE_GESTOR"
ROLE_USER = "ROLE_USER"


def require_roles(*roles):
    """Decorator para exigir que o usuário possua um dos papéis informados.

    A função tenta obter o papel atual a partir de ``g.current_role`` ou do
    cabeçalho ``X-Role``. Caso nenhum papel seja encontrado ou o papel não
    esteja entre os permitidos, a requisição é abortada com *403*.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            role = getattr(g, "current_role", None)
            if role is None:
                role = request.headers.get("X-Role")
            if role not in roles:
                abort(403)
            return func(*args, **kwargs)

        return wrapper

    return decorator
