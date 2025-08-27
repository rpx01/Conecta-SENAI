"""add turno to horarios

Revision ID: 5c1319886e69
Revises: 63791341500f
Create Date: 2025-08-27 14:14:34.499712

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c1319886e69'
down_revision: Union[str, Sequence[str], None] = '63791341500f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add coluna turno na tabela de horários."""
    turno_enum = sa.Enum(
        "MANHA",
        "TARDE",
        "NOITE",
        "MANHA_TARDE",
        "TARDE_NOITE",
        name="turno_enum",
    )
    turno_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "planejamento_horarios",
        sa.Column("turno", turno_enum, nullable=True),
    )
    op.create_index(
        op.f("ix_planejamento_horarios_turno"),
        "planejamento_horarios",
        ["turno"],
    )


def downgrade() -> None:
    """Remove coluna turno de horários."""
    op.drop_index(
        op.f("ix_planejamento_horarios_turno"),
        table_name="planejamento_horarios",
    )
    op.drop_column("planejamento_horarios", "turno")
    turno_enum = sa.Enum(
        "MANHA",
        "TARDE",
        "NOITE",
        "MANHA_TARDE",
        "TARDE_NOITE",
        name="turno_enum",
    )
    turno_enum.drop(op.get_bind(), checkfirst=True)
