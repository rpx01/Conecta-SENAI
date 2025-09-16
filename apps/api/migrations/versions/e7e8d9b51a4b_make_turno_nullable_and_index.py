"""make turno nullable and indexed"""
from alembic import op
import sqlalchemy as sa

revision = "e7e8d9b51a4b"
down_revision = "ddbb2c0823e0"
branch_labels = None
depends_on = None

TURNOS = ("Manhã", "Tarde", "Noite", "Manhã/Tarde", "Tarde/Noite")

def upgrade() -> None:
    op.alter_column(
        "planejamento_horarios",
        "turno",
        existing_type=sa.String(length=20),
        nullable=True,
    )
    op.drop_constraint(
        "ck_planejamento_horarios_turno",
        "planejamento_horarios",
        type_="check",
    )
    op.create_check_constraint(
        "ck_planejamento_horarios_turno",
        "planejamento_horarios",
        "turno IS NULL OR turno IN ('Manhã','Tarde','Noite','Manhã/Tarde','Tarde/Noite')",
    )
    op.execute("UPDATE planejamento_horarios SET turno='Manhã' WHERE turno='manhã'")
    op.execute("UPDATE planejamento_horarios SET turno='Tarde' WHERE turno='tarde'")
    op.execute("UPDATE planejamento_horarios SET turno='Noite' WHERE turno='noite'")
    op.execute("UPDATE planejamento_horarios SET turno='Manhã/Tarde' WHERE turno='manhã/tarde'")
    op.execute("UPDATE planejamento_horarios SET turno='Tarde/Noite' WHERE turno='tarde/noite'")
    op.create_index(
        "ix_planejamento_horarios_turno",
        "planejamento_horarios",
        ["turno"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_planejamento_horarios_turno",
        table_name="planejamento_horarios",
    )
    op.drop_constraint(
        "ck_planejamento_horarios_turno",
        "planejamento_horarios",
        type_="check",
    )
    op.create_check_constraint(
        "ck_planejamento_horarios_turno",
        "planejamento_horarios",
        "turno IN ('Manhã','Tarde','Noite','Manhã/Tarde','Tarde/Noite')",
    )
    op.alter_column(
        "planejamento_horarios",
        "turno",
        existing_type=sa.String(length=20),
        nullable=False,
    )
