"""create planejamento_itens table

Revision ID: d1b2c3d4e5f6
Revises: 9fd848c63563
Create Date: 2025-08-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '9fd848c63563'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'planejamento_itens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('row_id', sa.String(length=36), nullable=False),
        sa.Column('lote_id', sa.String(length=36), nullable=False),
        sa.Column('data', sa.Date(), nullable=False),
        sa.Column('semana', sa.String(length=20), nullable=True),
        sa.Column('horario', sa.String(length=50), nullable=True),
        sa.Column('carga_horaria', sa.String(length=50), nullable=True),
        sa.Column('modalidade', sa.String(length=50), nullable=True),
        sa.Column('treinamento', sa.String(length=100), nullable=True),
        sa.Column('cmd', sa.String(length=100), nullable=True),
        sa.Column('sjb', sa.String(length=100), nullable=True),
        sa.Column('sag_tombos', sa.String(length=100), nullable=True),
        sa.Column('instrutor', sa.String(length=100), nullable=True),
        sa.Column('local', sa.String(length=100), nullable=True),
        sa.Column('observacao', sa.String(length=255), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=True),
        sa.Column('atualizado_em', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('row_id'),
    )


def downgrade() -> None:
    op.drop_table('planejamento_itens')
