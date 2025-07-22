"""add status column to turmas_treinamento

Revision ID: 47aff0d3be81
Revises: 67c822ca4b6e
Create Date: 2025-08-22 13:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '47aff0d3be81'
down_revision: Union[str, Sequence[str], None] = '67c822ca4b6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE turmas_treinamento ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'aberta'")


def downgrade() -> None:
    op.execute("ALTER TABLE turmas_treinamento DROP COLUMN IF EXISTS status")
