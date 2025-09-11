"""add_teoria_online_to_turmas_treinamento

Revision ID: acbd43991573
Revises: aa0b6b279d7c
Create Date: 2025-09-11 00:30:50.814057

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'acbd43991573'
down_revision: Union[str, Sequence[str], None] = 'aa0b6b279d7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "turmas_treinamento",
        sa.Column("teoria_online", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("turmas_treinamento", "teoria_online", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("turmas_treinamento", "teoria_online")
