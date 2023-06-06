"""Invalidate ship sanctions cache

Revision ID: 1b09215e4fba
Revises: 15148a448dd1
Create Date: 2019-11-12 13:14:35.946851

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '1b09215e4fba'
down_revision = '15148a448dd1'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("TRUNCATE TABLE ship_sanctions")


def downgrade():
    pass
