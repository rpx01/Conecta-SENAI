"""add turno column to planejamento_horarios"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2e5a1b3c4d5e'
down_revision = 'cria_tabelas_base_planejamento'
branch_labels = None
depends_on = None

TURNOS = ('manhã', 'tarde', 'noite', 'manhã/tarde', 'tarde/noite')
turno_enum = sa.Enum(*TURNOS, name='turno_enum')


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        op.add_column(
            'planejamento_horarios',
            sa.Column('turno', sa.String(length=20), nullable=True),
        )
        op.create_check_constraint(
            'ck_planejamento_horarios_turno',
            'planejamento_horarios',
            "turno IN ('manhã','tarde','noite','manhã/tarde','tarde/noite')",
        )
    else:
        turno_enum.create(bind, checkfirst=True)
        op.add_column(
            'planejamento_horarios',
            sa.Column('turno', turno_enum, nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        op.drop_constraint(
            'ck_planejamento_horarios_turno',
            'planejamento_horarios',
            type_='check',
        )
        op.drop_column('planejamento_horarios', 'turno')
    else:
        op.drop_column('planejamento_horarios', 'turno')
        turno_enum.drop(bind, checkfirst=True)
