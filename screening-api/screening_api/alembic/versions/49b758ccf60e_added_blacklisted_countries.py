"""Added blacklisted countries

Revision ID: 49b758ccf60e
Revises: 00457f432986
Create Date: 2018-03-26 10:12:50.940173

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '49b758ccf60e'
down_revision = '00457f432986'
branch_labels = None
depends_on = None

severity = postgresql.ENUM(
    'OK', 'WARNING', 'CRITICAL', 'UNKNOWN',
    name='severity', create_type=False,
)


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'blacklisted_countries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('country_id', sa.String(), nullable=False),
        sa.Column('country_name', sa.String(), nullable=False),
        sa.Column('severity', severity, nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('country_id'),
        sa.UniqueConstraint('country_name'),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('blacklisted_countries')
    # ### end Alembic commands ###
