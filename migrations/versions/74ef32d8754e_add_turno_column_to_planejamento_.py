"""add turno column to planejamento_horarios

Revision ID: 74ef32d8754e
Revises: 63791341500f
Create Date: 2025-08-27 20:44:02.883818

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74ef32d8754e'
down_revision: Union[str, Sequence[str], None] = '63791341500f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("planejamento_horarios")]
    if "turno" not in columns:
        op.add_column(
            "planejamento_horarios",
            sa.Column("turno", sa.String(length=20), nullable=True),
        )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("planejamento_horarios")]
    if "turno" in columns:
        op.drop_column("planejamento_horarios", "turno")
