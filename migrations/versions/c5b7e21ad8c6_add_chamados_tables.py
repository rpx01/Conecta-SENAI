"""add tables for chamados module"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c5b7e21ad8c6'
down_revision: Union[str, Sequence[str], None] = 'c5c387dbd0a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(inspector: sa.Inspector, table: str) -> bool:
    return table in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, 'ticket_categories'):
        op.create_table(
            'ticket_categories',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('nome', sa.String(length=120), nullable=False, unique=True),
            sa.Column('descricao', sa.Text(), nullable=True),
            sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        )
    if not _table_exists(inspector, 'ticket_priorities'):
        op.create_table(
            'ticket_priorities',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('nome', sa.String(length=50), nullable=False, unique=True),
            sa.Column('peso', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        )
    if not _table_exists(inspector, 'ticket_statuses'):
        op.create_table(
            'ticket_statuses',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('nome', sa.String(length=50), nullable=False, unique=True),
            sa.Column('ordem', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        )
    if not _table_exists(inspector, 'ticket_locations'):
        op.create_table(
            'ticket_locations',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('nome', sa.String(length=120), nullable=False, unique=True),
            sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        )
    if not _table_exists(inspector, 'ticket_assets'):
        op.create_table(
            'ticket_assets',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('tag', sa.String(length=120), nullable=False, unique=True),
            sa.Column('descricao', sa.Text(), nullable=True),
            sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        )
    if not _table_exists(inspector, 'ticket_slas'):
        op.create_table(
            'ticket_slas',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('categoria_id', sa.Integer(), sa.ForeignKey('ticket_categories.id'), nullable=True),
            sa.Column('prioridade_id', sa.Integer(), sa.ForeignKey('ticket_priorities.id'), nullable=False),
            sa.Column('horas', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.UniqueConstraint('categoria_id', 'prioridade_id', name='uq_ticket_sla_categoria_prioridade'),
        )
    if not _table_exists(inspector, 'tickets'):
        op.create_table(
            'tickets',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('titulo', sa.String(length=200), nullable=False),
            sa.Column('descricao', sa.Text(), nullable=False),
            sa.Column('categoria_id', sa.Integer(), sa.ForeignKey('ticket_categories.id'), nullable=False),
            sa.Column('prioridade_id', sa.Integer(), sa.ForeignKey('ticket_priorities.id'), nullable=False),
            sa.Column('status_id', sa.Integer(), sa.ForeignKey('ticket_statuses.id'), nullable=False),
            sa.Column('solicitante_id', sa.Integer(), sa.ForeignKey('usuarios.id'), nullable=False),
            sa.Column('atribuido_id', sa.Integer(), sa.ForeignKey('usuarios.id'), nullable=True),
            sa.Column('location_id', sa.Integer(), sa.ForeignKey('ticket_locations.id'), nullable=True),
            sa.Column('asset_id', sa.Integer(), sa.ForeignKey('ticket_assets.id'), nullable=True),
            sa.Column('sla_horas', sa.Integer(), nullable=True),
            sa.Column('prazo_sla', sa.DateTime(), nullable=True),
            sa.Column('resolvido_em', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        )
        op.create_index('ix_tickets_status_id', 'tickets', ['status_id'])
        op.create_index('ix_tickets_categoria_id', 'tickets', ['categoria_id'])
        op.create_index('ix_tickets_prioridade_id', 'tickets', ['prioridade_id'])
        op.create_index('ix_tickets_solicitante_id', 'tickets', ['solicitante_id'])
        op.create_index('ix_tickets_atribuido_id', 'tickets', ['atribuido_id'])
        op.create_index('ix_tickets_created_at', 'tickets', ['created_at'])
    if not _table_exists(inspector, 'ticket_comments'):
        op.create_table(
            'ticket_comments',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('tickets.id'), nullable=False),
            sa.Column('autor_id', sa.Integer(), sa.ForeignKey('usuarios.id'), nullable=False),
            sa.Column('mensagem', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        )
    if not _table_exists(inspector, 'ticket_attachments'):
        op.create_table(
            'ticket_attachments',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('tickets.id'), nullable=False),
            sa.Column('filename', sa.String(length=255), nullable=False),
            sa.Column('content_type', sa.String(length=120), nullable=False),
            sa.Column('size_bytes', sa.Integer(), nullable=False),
            sa.Column('storage_path', sa.String(length=500), nullable=False),
            sa.Column('uploaded_by_id', sa.Integer(), sa.ForeignKey('usuarios.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table in [
        'ticket_attachments',
        'ticket_comments',
        'tickets',
        'ticket_slas',
        'ticket_assets',
        'ticket_locations',
        'ticket_statuses',
        'ticket_priorities',
        'ticket_categories',
    ]:
        if _table_exists(inspector, table):
            op.drop_table(table)
