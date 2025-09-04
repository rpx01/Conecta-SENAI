"""add teorico_online column to turmas_treinamento

Revision ID: b0c1d2e3f4a5
Revises: f1d2d74c8a7b
Create Date: 2025-08-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b0c1d2e3f4a5'
down_revision: Union[str, Sequence[str], None] = 'f1d2d74c8a7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('turmas_treinamento', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('teorico_online', sa.Boolean(), nullable=False, server_default=sa.text('false'))
        )


def downgrade() -> None:
    with op.batch_alter_table('turmas_treinamento', schema=None) as batch_op:
        batch_op.drop_column('teorico_online')
