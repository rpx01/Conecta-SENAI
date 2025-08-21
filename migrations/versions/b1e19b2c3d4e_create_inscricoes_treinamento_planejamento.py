"""create inscricoes_treinamento_planejamento table

Revision ID: b1e19b2c3d4e
Revises: 9f1c4e5a4b6a
Create Date: 2025-08-21 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b1e19b2c3d4e'
down_revision: Union[str, Sequence[str], None] = '9f1c4e5a4b6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'inscricoes_treinamento_planejamento',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('treinamento_id', sa.Integer, nullable=True),
        sa.Column('nome_treinamento', sa.String(length=255), nullable=False),
        sa.Column('matricula', sa.String(length=50), nullable=False),
        sa.Column('tipo_treinamento', sa.String(length=100), nullable=False),
        sa.Column('nome_completo', sa.String(length=255), nullable=False),
        sa.Column('naturalidade', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('data_nascimento', sa.Date, nullable=False),
        sa.Column('cpf', sa.String(length=14), nullable=False),
        sa.Column('empresa', sa.String(length=255), nullable=False),
        sa.Column('criado_em', sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table('inscricoes_treinamento_planejamento')
