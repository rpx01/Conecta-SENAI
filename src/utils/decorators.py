from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from src.models.user import User
from src.auth import verificar_autenticacao


def admin_required():
    """Decorator que garante que o usuário é administrador."""

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            user = None
            try:
                user_id = get_jwt_identity()
                if user_id:
                    user = User.query.get(user_id)
            except Exception:
                user = None
            if not user:
                autenticado, user = verificar_autenticacao(request)
                if not autenticado:
                    return jsonify({"erro": "Acesso restrito a administradores"}), 403
            if user and (user.is_admin() if callable(getattr(user, "is_admin", None)) else getattr(user, "is_admin", False)):
                return fn(*args, **kwargs)
            return jsonify({"erro": "Acesso restrito a administradores"}), 403

        return decorator

    return wrapper
