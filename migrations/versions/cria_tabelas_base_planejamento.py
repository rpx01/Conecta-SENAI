"""Cria tabelas base para o planejamento

Revision ID: cria_tabelas_base_planejamento
Revises: f1d2d74c8a7b
Create Date: 2025-08-18 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cria_tabelas_base_planejamento'
down_revision = 'f1d2d74c8a7b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'planejamento_bd_itens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('descricao', sa.String(), nullable=False),
        sa.Column('instrutor_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['instrutor_id'], ['instrutores.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'planejamento_cargas_horarias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome')
    )
    op.create_table(
        'planejamento_horarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome')
    )
    op.create_table(
        'planejamento_locais',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome')
    )
    op.create_table(
        'planejamento_modalidades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome')
    )
    op.create_table(
        'planejamento_publicos_alvo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome')
    )


def downgrade():
    op.drop_table('planejamento_publicos_alvo')
    op.drop_table('planejamento_modalidades')
    op.drop_table('planejamento_locais')
    op.drop_table('planejamento_horarios')
    op.drop_table('planejamento_cargas_horarias')
    op.drop_table('planejamento_bd_itens')
