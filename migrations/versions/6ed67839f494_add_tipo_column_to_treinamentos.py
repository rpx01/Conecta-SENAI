"""add tipo column to treinamentos"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '6ed67839f494'
down_revision: Union[str, Sequence[str], None] = '5e78c8e1a7b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('treinamentos', sa.Column('tipo', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('treinamentos', 'tipo')
