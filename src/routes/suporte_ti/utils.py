"""Utilitários compartilhados para as rotas do módulo de suporte de TI."""
from __future__ import annotations

from typing import Iterable

from sqlalchemy import inspect, text
from sqlalchemy.exc import ProgrammingError

from src.models import db
from src.models.suporte_chamado import SuporteChamado


def ensure_tables_exist(models: Iterable[type[db.Model]]) -> None:
    """Garante que as tabelas (e colunas críticas) existam antes do uso.

    Esta função mantém a compatibilidade com ambientes onde as migrações
    ainda não foram aplicadas totalmente. Além de criar tabelas ausentes,
    ela verifica e cria a coluna ``observacoes`` da tabela de chamados,
    necessária para que os modelos atuais funcionem corretamente.
    """

    inspector = inspect(db.engine)
    for model in models:
        table_name = model.__tablename__
        if not inspector.has_table(table_name):
            model.__table__.create(db.engine)
            inspector = inspect(db.engine)

        if table_name == SuporteChamado.__tablename__:
            inspector = _ensure_suporte_chamados_observacoes(inspector)


def _ensure_suporte_chamados_observacoes(inspector):
    """Garante que a coluna ``observacoes`` exista na tabela de chamados."""

    table_name = SuporteChamado.__tablename__
    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if "observacoes" in columns:
        return inspector

    ddl = text("ALTER TABLE suporte_chamados ADD COLUMN observacoes TEXT")
    try:
        with db.engine.begin() as connection:
            connection.execute(ddl)
    except ProgrammingError as exc:  # pragma: no cover - dependente do banco
        mensagem = str(exc).lower()
        if "duplicate column" not in mensagem and "already exists" not in mensagem:
            raise

    return inspect(db.engine)
