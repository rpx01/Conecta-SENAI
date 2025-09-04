"""add teorico_online to turmas

Revision ID: b6e3f5a1c9d0
Revises: f1d2d74c8a7b
Create Date: 2025-08-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6e3f5a1c9d0'
down_revision: Union[str, Sequence[str], None] = 'f1d2d74c8a7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'turmas_treinamento',
        sa.Column('teorico_online', sa.Boolean(), nullable=False, server_default=sa.text("0"))
    )


def downgrade() -> None:
    op.drop_column('turmas_treinamento', 'teorico_online')

