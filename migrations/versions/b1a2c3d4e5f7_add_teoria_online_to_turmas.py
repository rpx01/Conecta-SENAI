"""add teoria_online to turmas_treinamento

Revision ID: b1a2c3d4e5f7
Revises: aa0b6b279d7c
Create Date: 2025-09-10 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1a2c3d4e5f7'
down_revision: Union[str, Sequence[str], None] = 'aa0b6b279d7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'turmas_treinamento',
        sa.Column(
            'teoria_online',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column(
        'turmas_treinamento', 'teoria_online', server_default=None
    )


def downgrade() -> None:
    op.drop_column('turmas_treinamento', 'teoria_online')
