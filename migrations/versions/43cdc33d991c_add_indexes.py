"""add indexes

Revision ID: 43cdc33d991c
Revises: 9fd848c63563
Create Date: 2025-08-08 20:30:18.100939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43cdc33d991c'
down_revision: Union[str, Sequence[str], None] = '9fd848c63563'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('ix_agendamentos_data', 'agendamentos', ['data'], unique=False)
    op.create_index(op.f('ix_agendamentos_usuario_id'), 'agendamentos', ['usuario_id'], unique=False)
    op.create_index(op.f('ix_logs_agendamentos_usuario'), 'logs_agendamentos', ['usuario'], unique=False)
    op.create_index('ix_logs_agendamentos_data_agendamento', 'logs_agendamentos', ['data_agendamento'], unique=False)
    op.create_index(op.f('ix_log_lancamentos_rateio_instrutor_usuario'), 'log_lancamentos_rateio_instrutor', ['usuario'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_log_lancamentos_rateio_instrutor_usuario'), table_name='log_lancamentos_rateio_instrutor')
    op.drop_index('ix_logs_agendamentos_data_agendamento', table_name='logs_agendamentos')
    op.drop_index(op.f('ix_logs_agendamentos_usuario'), table_name='logs_agendamentos')
    op.drop_index(op.f('ix_agendamentos_usuario_id'), table_name='agendamentos')
    op.drop_index('ix_agendamentos_data', table_name='agendamentos')
