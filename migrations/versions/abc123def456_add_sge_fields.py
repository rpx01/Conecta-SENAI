"""add sge fields to planejamento_itens

Revision ID: abc123def456
Revises: 9fd848c63563
Create Date: 2025-08-07 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc123def456'
down_revision: Union[str, Sequence[str], None] = '9fd848c63563'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('planejamento_itens', sa.Column('sge_ativo', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('planejamento_itens', sa.Column('sge_link', sa.String(length=512), nullable=True))
    op.alter_column('planejamento_itens', 'sge_ativo', server_default=None)


def downgrade() -> None:
    op.drop_column('planejamento_itens', 'sge_link')
    op.drop_column('planejamento_itens', 'sge_ativo')
