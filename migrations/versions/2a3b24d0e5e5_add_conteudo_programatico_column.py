"""add conteudo_programatico column to treinamentos

Revision ID: add_conteudo_programatico
Revises: 9f1c4e5a4b6a
Create Date: 2025-09-01 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'add_conteudo_programatico'
down_revision: Union[str, Sequence[str], None] = '9f1c4e5a4b6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('treinamentos', sa.Column('conteudo_programatico', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('treinamentos', 'conteudo_programatico')
