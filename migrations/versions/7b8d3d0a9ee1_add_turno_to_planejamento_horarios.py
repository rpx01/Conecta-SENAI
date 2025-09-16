from alembic import op
import sqlalchemy as sa

# Revisões
revision = "7b8d3d0a9ee1"
down_revision = "cria_tabelas_base_planejamento"
branch_labels = None
depends_on = None

TURNOS = ("manhã", "tarde", "noite", "manhã/tarde", "tarde/noite")


def upgrade():
    """Adiciona coluna turno à tabela de horários."""
    op.add_column(
        "planejamento_horarios",
        sa.Column(
            "turno",
            sa.String(length=20),
            nullable=False,
            server_default="manhã",
        ),
    )

    op.create_check_constraint(
        "ck_planejamento_horarios_turno",
        "planejamento_horarios",
        (
            "turno IN ('manhã','tarde','noite','manhã/tarde','tarde/noite')"
        ),
    )

    op.alter_column("planejamento_horarios", "turno", server_default=None)


def downgrade():
    op.drop_constraint(
        "ck_planejamento_horarios_turno",
        "planejamento_horarios",
        type_="check",
    )
    op.drop_column("planejamento_horarios", "turno")
