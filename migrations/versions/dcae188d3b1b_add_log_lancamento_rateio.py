"""Cria tabela de logs de lancamentos de rateio"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'dcae188d3b1b'
down_revision = '4b18c0688af2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'log_lancamentos_rateio_instrutor',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('timestamp', sa.DateTime, nullable=True),
        sa.Column('acao', sa.String(length=20), nullable=True),
        sa.Column('usuario', sa.String(length=100), nullable=True),
        sa.Column('instrutor', sa.String(length=100), nullable=True),
        sa.Column('filial', sa.String(length=100), nullable=True),
        sa.Column('uo', sa.String(length=100), nullable=True),
        sa.Column('cr', sa.String(length=100), nullable=True),
        sa.Column('classe_valor', sa.String(length=100), nullable=True),
        sa.Column('percentual', sa.Float, nullable=True),
        sa.Column('observacao', sa.Text, nullable=True),
    )


def downgrade():
    op.drop_table('log_lancamentos_rateio_instrutor')
