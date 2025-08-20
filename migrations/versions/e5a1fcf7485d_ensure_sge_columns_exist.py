"""Ensure sge columns exist in planejamento_itens"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e5a1fcf7485d"
down_revision = "a3e4f5d6c7b8"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("planejamento_itens")}

    if "sge_ativo" not in columns:
        op.add_column(
            "planejamento_itens",
            sa.Column("sge_ativo", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        op.alter_column("planejamento_itens", "sge_ativo", server_default=None)

    if "sge_link" not in columns:
        op.add_column(
            "planejamento_itens",
            sa.Column("sge_link", sa.String(length=512), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("planejamento_itens")}

    if "sge_link" in columns:
        op.drop_column("planejamento_itens", "sge_link")
    if "sge_ativo" in columns:
        op.drop_column("planejamento_itens", "sge_ativo")
