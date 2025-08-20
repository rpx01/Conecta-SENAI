"""Add SGE fields to planejamento_itens

Revision ID: a3e4f5d6c7b8
Revises: 1faac30c7383
Create Date: 2025-08-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a3e4f5d6c7b8'
down_revision = '1faac30c7383'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'planejamento_itens',
        sa.Column('sge_ativo', sa.Boolean(), server_default=sa.text('false')),
    )
    op.add_column(
        'planejamento_itens',
        sa.Column('sge_link', sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('planejamento_itens', 'sge_link')
    op.drop_column('planejamento_itens', 'sge_ativo')
