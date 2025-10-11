"""add data_evento to noticias"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d5d3c6b59b5d"
down_revision: Union[str, Sequence[str], None] = "c5c387dbd0a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE_NAME = "noticias"
COLUMN_NAME = "data_evento"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table(TABLE_NAME):
        return

    columns = {column["name"] for column in inspector.get_columns(TABLE_NAME)}
    if COLUMN_NAME in columns:
        return

    op.add_column(
        TABLE_NAME,
        sa.Column(COLUMN_NAME, sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table(TABLE_NAME):
        return

    columns = {column["name"] for column in inspector.get_columns(TABLE_NAME)}
    if COLUMN_NAME not in columns:
        return

    op.drop_column(TABLE_NAME, COLUMN_NAME)
