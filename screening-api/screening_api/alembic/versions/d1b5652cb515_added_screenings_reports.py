"""Added screenings reports

Revision ID: d1b5652cb515
Revises: 91e02632f1df
Create Date: 2018-01-25 14:36:58.726529

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1b5652cb515'
down_revision = '91e02632f1df'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'screenings_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('screening_id', sa.Integer(), nullable=False),
        sa.Column('company_sanctions', sa.JSON(), nullable=True),
        sa.Column('ship_association', sa.JSON(), nullable=True),
        sa.Column('ship_sanction', sa.JSON(), nullable=True),
        sa.Column('ship_flag', sa.JSON(), nullable=True),
        sa.Column('ship_registered_owner', sa.JSON(), nullable=True),
        sa.Column('ship_operator', sa.JSON(), nullable=True),
        sa.Column('ship_beneficial_owner', sa.JSON(), nullable=True),
        sa.Column('ship_manager', sa.JSON(), nullable=True),
        sa.Column('ship_technical_manager', sa.JSON(), nullable=True),
        sa.Column('doc_company', sa.JSON(), nullable=True),
        sa.Column('ship_inspections', sa.JSON(), nullable=True),
        sa.Column('port_visits', sa.JSON(), nullable=True),
        sa.Column('zone_visits', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ['screening_id'], ['screenings.id'],
            onupdate='CASCADE', ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('screenings_reports')
    # ### end Alembic commands ###
