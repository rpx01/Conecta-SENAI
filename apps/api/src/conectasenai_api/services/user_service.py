"""Serviços relacionados a operações de usuário."""

from typing import Tuple, Optional, Dict, Any

from sqlalchemy.exc import SQLAlchemyError

from conectasenai_common.validators import PASSWORD_REGEX
from conectasenai_api.models.user import User
from conectasenai_api.repositories.user_repository import UserRepository


def criar_usuario(dados: Dict[str, Any]) -> Tuple[Optional[User], Optional[Tuple[Dict[str, str], int]]]:
    """Valida e cria um novo usuário.

    Args:
        dados: Dicionário com as informações do usuário.

    Returns:
        Uma tupla contendo o usuário criado ou ``None`` em caso de erro, e
        opcionalmente um tupla ``(mensagem, status)`` quando houver erro de
        validação.
    """
    nome = dados.get("nome")
    email = dados.get("email")
    senha = dados.get("senha")
    username = dados.get("username") or (email.split("@")[0] if email else "")

    if UserRepository.get_by_email(email):
        return None, ({"erro": "Email já cadastrado"}, 400)

    try:
        novo_usuario = User(
            nome=nome,
            email=email,
            senha=senha,
            tipo="comum",
            username=username,
        )
        UserRepository.add(novo_usuario)
        return novo_usuario, None
    except SQLAlchemyError as e:  # pragma: no cover - erros de banco
        UserRepository.rollback()
        raise e
