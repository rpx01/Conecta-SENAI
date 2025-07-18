"""Adiciona coluna max_alunos em Treinamento

Revision ID: 67a52a1d4e3a
Revises: dcae188d3b1b
Create Date: 2025-07-18 01:18:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '67a52a1d4e3a'
down_revision = 'dcae188d3b1b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('treinamentos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('max_alunos', sa.Integer(), nullable=False, server_default='0'))
    with op.batch_alter_table('treinamentos', schema=None) as batch_op:
        batch_op.alter_column('max_alunos', server_default=None)


def downgrade():
    with op.batch_alter_table('treinamentos', schema=None) as batch_op:
        batch_op.drop_column('max_alunos')
