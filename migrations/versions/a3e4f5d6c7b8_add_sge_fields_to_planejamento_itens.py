"""add sge fields to planejamento_itens"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a3e4f5d6c7b8"
down_revision = "1faac30c7383"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "planejamento_itens",
        sa.Column(
            "sge_ativo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "planejamento_itens",
        sa.Column("sge_link", sa.String(length=512), nullable=True),
    )
    op.alter_column("planejamento_itens", "sge_ativo", server_default=None)


def downgrade() -> None:
    op.drop_column("planejamento_itens", "sge_link")
    op.drop_column("planejamento_itens", "sge_ativo")
