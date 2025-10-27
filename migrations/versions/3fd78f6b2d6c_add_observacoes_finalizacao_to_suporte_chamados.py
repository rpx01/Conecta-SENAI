"""Add observacoes_finalizacao column to suporte_chamados

Revision ID: 3fd78f6b2d6c
Revises: 0c016820b114
Create Date: 2025-08-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3fd78f6b2d6c'
down_revision = '0c016820b114'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'suporte_chamados',
        sa.Column('observacoes_finalizacao', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('suporte_chamados', 'observacoes_finalizacao')
