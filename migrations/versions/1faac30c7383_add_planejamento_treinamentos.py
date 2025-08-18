"""Add planejamento_treinamentos

Revision ID: 1faac30c7383
Revises: merge_planejamento_branch
Create Date: 2025-08-18 21:42:12.683074

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1faac30c7383'
down_revision: Union[str, Sequence[str], None] = 'merge_planejamento_branch'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'planejamento_treinamentos',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nome', sa.String(length=120), nullable=False, unique=True),
        sa.Column('carga_horaria', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('planejamento_treinamentos')
