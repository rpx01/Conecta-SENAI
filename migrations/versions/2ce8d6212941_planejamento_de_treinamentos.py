"""Planejamento de Treinamentos

Revision ID: 2ce8d6212941
Revises: 18fee14ce212
Create Date: 2025-08-13 15:05:20.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "2ce8d6212941"
down_revision: Union[str, Sequence[str], None] = "18fee14ce212"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create planejamento table."""
    op.create_table(
        "planejamento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column(
            "turno",
            sa.Enum("MANHA", "TARDE", "NOITE", name="turno_enum"),
            nullable=False,
        ),
        sa.Column("carga_horas", sa.Integer(), nullable=True),
        sa.Column(
            "modalidade",
            sa.Enum("Presencial", "Online", name="modalidade_enum"),
            nullable=True,
        ),
        sa.Column("treinamento", sa.String(length=255), nullable=False),
        sa.Column("instrutor_id", sa.Integer(), nullable=False),
        sa.Column("local", sa.String(length=255), nullable=True),
        sa.Column("cliente", sa.String(length=120), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "Planejado",
                "Confirmado",
                "Cancelado",
                name="status_enum",
            ),
            nullable=False,
            server_default="Planejado",
        ),
        sa.Column(
            "origem",
            sa.Enum("Manual", "Importado", name="origem_enum"),
            nullable=False,
            server_default="Manual",
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("atualizado_em", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["instrutor_id"], ["instrutores.id"]),
        sa.UniqueConstraint(
            "data",
            "turno",
            "instrutor_id",
            name="uq_planejamento_slot_instrutor",
        ),
    )
    op.create_index(
        op.f("ix_planejamento_data"), "planejamento", ["data"], unique=False
    )
    op.create_index(
        op.f("ix_planejamento_instrutor_id"),
        "planejamento",
        ["instrutor_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop planejamento table."""
    op.drop_index(
        op.f("ix_planejamento_instrutor_id"), table_name="planejamento"
    )
    op.drop_index(op.f("ix_planejamento_data"), table_name="planejamento")
    op.drop_table("planejamento")
    sa.Enum(name="origem_enum").drop(op.get_bind(), checkfirst=False)
    sa.Enum(name="status_enum").drop(op.get_bind(), checkfirst=False)
    sa.Enum(name="modalidade_enum").drop(op.get_bind(), checkfirst=False)
    sa.Enum(name="turno_enum").drop(op.get_bind(), checkfirst=False)
