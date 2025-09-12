"""add fields to secretaria_treinamentos

Revision ID: bbf42e5bd6b0
Revises: 8055be39141c
Create Date: 2025-11-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'bbf42e5bd6b0'
down_revision: Union[str, Sequence[str], None] = '8055be39141c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new columns to secretaria_treinamentos table if missing."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("secretaria_treinamentos"):
        cols = {c["name"] for c in inspector.get_columns("secretaria_treinamentos")}
        if "ativo" not in cols:
            op.add_column(
                "secretaria_treinamentos",
                sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
            )
            op.create_index(
                op.f("ix_secretaria_treinamentos_ativo"),
                "secretaria_treinamentos",
                ["ativo"],
            )
        if "created_at" not in cols:
            op.add_column(
                "secretaria_treinamentos",
                sa.Column(
                    "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
                ),
            )
        if "updated_at" not in cols:
            op.add_column(
                "secretaria_treinamentos",
                sa.Column(
                    "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
                ),
            )
        # Tornar nome opcional
        colinfo = inspector.get_columns("secretaria_treinamentos")
        for c in colinfo:
            if c["name"] == "nome" and not c["nullable"]:
                op.alter_column(
                    "secretaria_treinamentos",
                    "nome",
                    existing_type=sa.String(length=255),
                    nullable=True,
                )
    else:
        op.create_table(
            "secretaria_treinamentos",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("nome", sa.String(length=255), nullable=True),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column(
                "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
            ),
            sa.Column(
                "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
            ),
        )
        op.create_index(
            op.f("ix_secretaria_treinamentos_email"),
            "secretaria_treinamentos",
            ["email"],
            unique=True,
        )
        op.create_index(
            op.f("ix_secretaria_treinamentos_ativo"),
            "secretaria_treinamentos",
            ["ativo"],
        )


def downgrade() -> None:
    """Revert changes."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("secretaria_treinamentos"):
        cols = {c["name"] for c in inspector.get_columns("secretaria_treinamentos")}
        if "ativo" in cols:
            op.drop_index(op.f("ix_secretaria_treinamentos_ativo"), table_name="secretaria_treinamentos")
            op.drop_column("secretaria_treinamentos", "ativo")
        if "created_at" in cols:
            op.drop_column("secretaria_treinamentos", "created_at")
        if "updated_at" in cols:
            op.drop_column("secretaria_treinamentos", "updated_at")
        # Voltar nome para not null se existia antes (best effort)
        op.alter_column(
            "secretaria_treinamentos",
            "nome",
            existing_type=sa.String(length=255),
            nullable=False,
        )
    else:
        op.drop_table("secretaria_treinamentos")
