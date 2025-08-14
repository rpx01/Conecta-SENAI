"""Planejamento de Treinamentos"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a8b9c0d1e2f3'
down_revision = '9fd848c63563'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'planejamento',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('data', sa.Date(), nullable=False),
        sa.Column('turno', sa.Enum('MANHA', 'TARDE', 'NOITE', name='turno_enum'), nullable=False),
        sa.Column('carga_horas', sa.Integer(), nullable=True),
        sa.Column('modalidade', sa.Enum('Presencial', 'Online', name='modalidade_enum'), nullable=True),
        sa.Column('treinamento', sa.String(length=255), nullable=False),
        sa.Column('instrutor_id', sa.Integer(), nullable=False),
        sa.Column('local', sa.String(length=255), nullable=True),
        sa.Column('cliente', sa.String(length=120), nullable=True),
        sa.Column('observacao', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('Planejado', 'Confirmado', 'Cancelado', name='status_enum'), nullable=False, server_default='Planejado'),
        sa.Column('origem', sa.Enum('Manual', 'Importado', name='origem_enum'), nullable=False, server_default='Manual'),
        sa.Column('criado_em', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('atualizado_em', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['instrutor_id'], ['instrutores.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('data', 'turno', 'instrutor_id', name='uq_planejamento_slot_instrutor')
    )
    op.create_index(op.f('ix_planejamento_data'), 'planejamento', ['data'], unique=False)
    op.create_index(op.f('ix_planejamento_instrutor_id'), 'planejamento', ['instrutor_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_planejamento_instrutor_id'), table_name='planejamento')
    op.drop_index(op.f('ix_planejamento_data'), table_name='planejamento')
    op.drop_table('planejamento')
    sa.Enum(name='turno_enum').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='modalidade_enum').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='status_enum').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='origem_enum').drop(op.get_bind(), checkfirst=False)
