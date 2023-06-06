"""Renamed bulk screening result

Revision ID: 60b052c7c1bf
Revises: ec2812bcfe1e
Create Date: 2018-11-12 14:37:43.051166

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '60b052c7c1bf'
down_revision = 'ec2812bcfe1e'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('screenings_bulk', 'result', new_column_name='status')
    op.execute("ALTER TYPE bulkscreeningstatus ADD VALUE 'DONE'")
    op.execute("ALTER TYPE bulkscreeningstatus ADD VALUE 'SCHEDULED'")


def downgrade():
    op.alter_column('screenings_bulk', 'status', new_column_name='result')
