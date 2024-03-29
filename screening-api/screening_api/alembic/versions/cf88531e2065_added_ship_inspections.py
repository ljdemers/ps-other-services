"""Added ship inspections

Revision ID: cf88531e2065
Revises: d421ff606ca6
Create Date: 2017-12-15 09:31:06.794264

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf88531e2065'
down_revision = 'd421ff606ca6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'ship_inspections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('ship_id', sa.Integer(), nullable=False),
        sa.Column('inspection_date', sa.DateTime(), nullable=False),
        sa.Column('detained_days', sa.Float(), nullable=False),
        sa.Column('defects_count', sa.Integer(), nullable=False),
        sa.Column('port_name', sa.String(), nullable=True),
        sa.Column('country_name', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ['ship_id'], ['ships.id'], onupdate='CASCADE', ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ship_inspections')
    # ### end Alembic commands ###
