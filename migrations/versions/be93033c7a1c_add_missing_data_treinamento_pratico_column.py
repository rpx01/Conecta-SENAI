"""ensure data_treinamento_pratico exists on turmas_treinamento

Revision ID: be93033c7a1c
Revises: bfad9cd914dc
Create Date: 2025-08-22 12:20:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'be93033c7a1c'
down_revision: Union[str, Sequence[str], None] = 'bfad9cd914dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE turmas_treinamento ADD COLUMN IF NOT EXISTS data_treinamento_pratico DATE")


def downgrade() -> None:
    op.execute("ALTER TABLE turmas_treinamento DROP COLUMN IF EXISTS data_treinamento_pratico")
