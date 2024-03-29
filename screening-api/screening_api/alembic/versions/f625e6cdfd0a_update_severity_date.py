"""Update severity date

Revision ID: f625e6cdfd0a
Revises: 5aacd59bf612
Create Date: 2018-07-26 13:47:51.378844

"""
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f625e6cdfd0a'
down_revision = '5aacd59bf612'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        'screenings_history', 'severity_date',
        existing_type=postgresql.TIMESTAMP(), nullable=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        'screenings_history', 'severity_date',
        existing_type=postgresql.TIMESTAMP(), nullable=True,
    )
    # ### end Alembic commands ###
