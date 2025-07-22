"""ensure data_termino exists on turmas_treinamento

Revision ID: bfad9cd914dc
Revises: 64b22f54fe47
Create Date: 2025-08-22 12:15:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'bfad9cd914dc'
down_revision: Union[str, Sequence[str], None] = '64b22f54fe47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE turmas_treinamento ADD COLUMN IF NOT EXISTS data_termino DATE")


def downgrade() -> None:
    op.execute("ALTER TABLE turmas_treinamento DROP COLUMN IF EXISTS data_termino")
