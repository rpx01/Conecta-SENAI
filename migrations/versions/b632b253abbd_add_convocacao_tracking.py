"""add convocacao tracking

Revision ID: b632b253abbd
Revises: 1c02b7a6da56
Create Date: 2025-09-11 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b632b253abbd'
down_revision: Union[str, Sequence[str], None] = '1c02b7a6da56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('inscricoes_treinamento') as batch_op:
        batch_op.add_column(sa.Column('convocado_por', sa.String(length=120), nullable=True))
        batch_op.alter_column('convocado_em', type_=sa.DateTime(timezone=True))
    op.create_index(
        'ix_insc_turma_convocado',
        'inscricoes_treinamento',
        ['turma_id', 'convocado_em'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_insc_turma_convocado', table_name='inscricoes_treinamento')
    with op.batch_alter_table('inscricoes_treinamento') as batch_op:
        batch_op.alter_column('convocado_em', type_=sa.DateTime(timezone=False))
        batch_op.drop_column('convocado_por')
