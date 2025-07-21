"""Adiciona cpf, data de nascimento e empresa ao usuario

Revision ID: 4ab146b87484
Revises: 
Create Date: 2025-07-21 19:07:13.104421

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4ab146b87484'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add new optional user fields."""
    op.add_column('usuarios', sa.Column('cpf', sa.String(length=14), nullable=True))
    op.add_column('usuarios', sa.Column('data_nascimento', sa.Date(), nullable=True))
    op.add_column('usuarios', sa.Column('empresa', sa.String(length=100), nullable=True))


def downgrade():
    """Remove user fields added in upgrade."""
    op.drop_column('usuarios', 'empresa')
    op.drop_column('usuarios', 'data_nascimento')
    op.drop_column('usuarios', 'cpf')
