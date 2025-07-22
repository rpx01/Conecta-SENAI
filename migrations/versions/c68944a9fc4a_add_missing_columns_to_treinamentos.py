"""ensure extra columns exist on treinamentos table

Revision ID: c68944a9fc4a
Revises: da712fed38d7
Create Date: 2025-08-22 12:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c68944a9fc4a'
down_revision: Union[str, Sequence[str], None] = 'da712fed38d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE treinamentos ADD COLUMN IF NOT EXISTS tem_pratica BOOLEAN")
    op.execute("ALTER TABLE treinamentos ADD COLUMN IF NOT EXISTS links_materiais JSONB")
    op.execute("ALTER TABLE treinamentos ADD COLUMN IF NOT EXISTS data_criacao TIMESTAMP")
    op.execute("ALTER TABLE treinamentos ADD COLUMN IF NOT EXISTS data_atualizacao TIMESTAMP")


def downgrade() -> None:
    op.execute("ALTER TABLE treinamentos DROP COLUMN IF EXISTS data_atualizacao")
    op.execute("ALTER TABLE treinamentos DROP COLUMN IF EXISTS data_criacao")
    op.execute("ALTER TABLE treinamentos DROP COLUMN IF EXISTS links_materiais")
    op.execute("ALTER TABLE treinamentos DROP COLUMN IF EXISTS tem_pratica")

