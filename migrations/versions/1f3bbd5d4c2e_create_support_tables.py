"""create support module tables"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1f3bbd5d4c2e"
down_revision: Union[str, Sequence[str], None] = "c5c387dbd0a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TIMESTAMP_DEFAULT = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "support_areas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("descricao", sa.String(length=255), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=TIMESTAMP_DEFAULT),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False, server_default=TIMESTAMP_DEFAULT),
    )
    op.create_index("uq_support_areas_nome", "support_areas", ["nome"], unique=True)

    op.create_table(
        "support_equipment_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("descricao", sa.String(length=255), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=TIMESTAMP_DEFAULT),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False, server_default=TIMESTAMP_DEFAULT),
    )
    op.create_index(
        "uq_support_equipment_types_nome",
        "support_equipment_types",
        ["nome"],
        unique=True,
    )

    op.create_table(
        "support_tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("area_id", sa.Integer(), sa.ForeignKey("support_areas.id"), nullable=True),
        sa.Column(
            "equipamento_id",
            sa.Integer(),
            sa.ForeignKey("support_equipment_types.id"),
            nullable=True,
        ),
        sa.Column("patrimonio", sa.String(length=100), nullable=True),
        sa.Column("numero_serie", sa.String(length=100), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("urgencia", sa.String(length=20), nullable=False, server_default=sa.text("'baixa'")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'aberto'")),
        sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=TIMESTAMP_DEFAULT),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False, server_default=TIMESTAMP_DEFAULT),
        sa.Column("resolvido_em", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_support_tickets_usuario", "support_tickets", ["usuario_id"])
    op.create_index("ix_support_tickets_area", "support_tickets", ["area_id"])
    op.create_index("ix_support_tickets_equipamento", "support_tickets", ["equipamento_id"])
    op.create_index("ix_support_tickets_status", "support_tickets", ["status"])
    op.create_index("ix_support_tickets_urgencia", "support_tickets", ["urgencia"])

    op.create_table(
        "support_ticket_attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "ticket_id",
            sa.Integer(),
            sa.ForeignKey("support_tickets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nome_arquivo", sa.String(length=255), nullable=False),
        sa.Column("caminho_relativo", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=TIMESTAMP_DEFAULT),
    )
    op.create_index(
        "ix_support_ticket_attachments_ticket", "support_ticket_attachments", ["ticket_id"]
    )

    op.create_table(
        "horarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("turno", sa.String(length=40), nullable=True),
    )


def downgrade() -> None:
    op.drop_index("ix_support_ticket_attachments_ticket", table_name="support_ticket_attachments")
    op.drop_table("support_ticket_attachments")
    op.drop_index("ix_support_tickets_urgencia", table_name="support_tickets")
    op.drop_index("ix_support_tickets_status", table_name="support_tickets")
    op.drop_index("ix_support_tickets_equipamento", table_name="support_tickets")
    op.drop_index("ix_support_tickets_area", table_name="support_tickets")
    op.drop_index("ix_support_tickets_usuario", table_name="support_tickets")
    op.drop_table("support_tickets")
    op.drop_index("uq_support_equipment_types_nome", table_name="support_equipment_types")
    op.drop_table("support_equipment_types")
    op.drop_index("uq_support_areas_nome", table_name="support_areas")
    op.drop_table("support_areas")
    op.drop_table("horarios")
