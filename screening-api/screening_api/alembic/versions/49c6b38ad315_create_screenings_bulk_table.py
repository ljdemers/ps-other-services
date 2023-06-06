"""create screenings bulk table

Revision ID: 49c6b38ad315
Revises:
Create Date: 2017-09-27 11:30:41.685592

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '49c6b38ad315'
down_revision = None
branch_labels = None
depends_on = None

bulkscreeningstatus = postgresql.ENUM(
    'PENDING', 'OK', 'INVALID', name='bulkscreeningstatus',
)


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'screenings_bulk',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column(
            'created', postgresql.TIMESTAMP(), autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            'updated', postgresql.TIMESTAMP(), autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            'account_id', sa.INTEGER(), autoincrement=False, nullable=False,
        ),
        sa.Column('imo_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column(
            'result', bulkscreeningstatus,
            autoincrement=False, nullable=False, default='PENDING',
        ),
        sa.PrimaryKeyConstraint('id', name='screenings_bulk_pkey'),
        sa.UniqueConstraint(
            'account_id', 'imo_id', name='account_id_imo_id_unique')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('screenings_bulk')
    bulkscreeningstatus.drop(op.get_bind(), checkfirst=False)
    # ### end Alembic commands ###
