"""Serviços relacionados a operações de usuário."""

import re
from typing import Tuple, Optional, Dict, Any

from sqlalchemy.exc import SQLAlchemyError

from src.models import db
from src.models.user import User

# Expressão regular para validar senhas
PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")


def criar_usuario(dados: Dict[str, Any]) -> Tuple[Optional[User], Optional[Tuple[Dict[str, str], int]]]:
    """Valida e cria um novo usuário.

    Args:
        dados: Dicionário com as informações do usuário.

    Returns:
        Uma tupla contendo o usuário criado ou ``None`` em caso de erro, e
        opcionalmente um tupla ``(mensagem, status)`` quando houver erro de
        validação.
    """
    nome = dados.get("nome", "").strip()
    email = dados.get("email", "").strip()
    senha = dados.get("senha")
    confirmar = dados.get("confirmarSenha")
    username = dados.get("username") or (email.split("@")[0] if email else "")

    if not all([nome, email, senha]):
        return None, ({"erro": "Dados incompletos"}, 400)

    if "confirmarSenha" in dados and not confirmar:
        return None, ({"erro": "Dados incompletos"}, 400)

    if confirmar is not None and senha != confirmar:
        return None, ({"erro": "As senhas não coincidem"}, 400)

    if User.query.filter_by(email=email).first():
        return None, ({"erro": "Este e-mail já está registado"}, 400)

    if not PASSWORD_REGEX.match(senha):
        return (
            None,
            (
                {
                    "erro": "Senha deve ter ao menos 8 caracteres, incluindo letra maiúscula, letra minúscula, número e caractere especial"
                },
                400,
            ),
        )

    try:
        novo_usuario = User(
            nome=nome,
            email=email,
            senha=senha,
            tipo="comum",
            username=username,
        )
        db.session.add(novo_usuario)
        db.session.commit()
        return novo_usuario, None
    except SQLAlchemyError as e:  # pragma: no cover - erros de banco
        db.session.rollback()
        raise e
