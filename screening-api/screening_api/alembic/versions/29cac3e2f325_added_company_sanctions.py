"""Added company sanctions

Revision ID: 29cac3e2f325
Revises: a1a469d97e6b
Create Date: 2018-04-27 10:53:51.608895

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '29cac3e2f325'
down_revision = 'a1a469d97e6b'
branch_labels = None
depends_on = None


shipassociatetype = sa.Enum(
    'GROUP_BENEFICIAL_OWNER', 'OPERATOR', 'REGISTERED_OWNER', 'SHIP_MANAGER',
    'TECHNICAL_MANAGER', name='shipassociatetype',
)
severity = postgresql.ENUM(
    'OK', 'WARNING', 'CRITICAL', 'UNKNOWN',
    name='severity', create_type=False,
)


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'company_sanctions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('ship_id', sa.Integer(), nullable=False),
        sa.Column('ship_associate_type', shipassociatetype, nullable=False),
        sa.Column('severity', severity, nullable=False),
        sa.Column('sanction_list_name', sa.String(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ['ship_id'], ['ships.id'], onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'ship_id', 'ship_associate_type', 'sanction_list_name',
            name='ship_id_ship_associate_type_sanction_list_name',
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('company_sanctions')
    # ### end Alembic commands ###
