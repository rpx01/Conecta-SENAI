"""Ensure turno column exists in planejamento_horarios"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ddbb2c0823e0"
down_revision = "7b8d3d0a9ee1"
branch_labels = None
depends_on = None

TURNOS = ("manhã", "tarde", "noite", "manhã/tarde", "tarde/noite")

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("planejamento_horarios")}

    if "turno" not in columns:
        op.add_column(
            "planejamento_horarios",
            sa.Column("turno", sa.String(length=20), nullable=False, server_default="manhã"),
        )
        op.create_check_constraint(
            "ck_planejamento_horarios_turno",
            "planejamento_horarios",
            "turno IN ('manhã','tarde','noite','manhã/tarde','tarde/noite')",
        )
        op.alter_column("planejamento_horarios", "turno", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("planejamento_horarios")}

    constraints = {c["name"] for c in inspector.get_check_constraints("planejamento_horarios")}

    if "ck_planejamento_horarios_turno" in constraints:
        op.drop_constraint(
            "ck_planejamento_horarios_turno",
            "planejamento_horarios",
            type_="check",
        )
    if "turno" in columns:
        op.drop_column("planejamento_horarios", "turno")
