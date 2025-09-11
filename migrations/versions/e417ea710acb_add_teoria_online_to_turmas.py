"""Add teoria_online to turmas

Revision ID: e417ea710acb
Revises: 74ef32d8754e
Create Date: 2025-09-11 00:34:47.408411

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e417ea710acb'
down_revision: Union[str, Sequence[str], None] = '74ef32d8754e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "turmas_treinamento",
        sa.Column(
            "teoria_online",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("turmas_treinamento", "teoria_online", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("turmas_treinamento", "teoria_online")
