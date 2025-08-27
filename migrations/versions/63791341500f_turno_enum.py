"""turno enum

Revision ID: 63791341500f
Revises: e7e8d9b51a4b
Create Date: 2025-08-26 23:56:27.074371

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63791341500f'
down_revision: Union[str, Sequence[str], None] = 'e7e8d9b51a4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    turno_enum = sa.Enum(
        'manha', 'tarde', 'noite', 'manha_tarde', 'tarde_noite', name='turno_enum'
    )
    turno_enum.create(op.get_bind(), checkfirst=True)
    op.alter_column(
        'planejamento_horarios',
        'turno',
        existing_type=sa.String(length=20),
        type_=turno_enum,
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'planejamento_horarios',
        'turno',
        existing_type=sa.Enum(
            'manha', 'tarde', 'noite', 'manha_tarde', 'tarde_noite', name='turno_enum'
        ),
        type_=sa.String(length=20),
        nullable=True,
    )
    sa.Enum(
        'manha', 'tarde', 'noite', 'manha_tarde', 'tarde_noite', name='turno_enum'
    ).drop(op.get_bind(), checkfirst=True)
