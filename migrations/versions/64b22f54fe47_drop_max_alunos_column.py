"""drop obsolete max_alunos column

Revision ID: 64b22f54fe47
Revises: c68944a9fc4a
Create Date: 2025-07-22 18:52:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '64b22f54fe47'
down_revision: Union[str, Sequence[str], None] = 'c68944a9fc4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE treinamentos DROP COLUMN IF EXISTS max_alunos")


def downgrade() -> None:
    op.execute("ALTER TABLE treinamentos ADD COLUMN IF NOT EXISTS max_alunos INTEGER NOT NULL DEFAULT 20")
    op.execute("ALTER TABLE treinamentos ALTER COLUMN max_alunos DROP DEFAULT")
