"""Renamed compliance_id to code

Revision ID: 876cd219b280
Revises: 0848f178fb1e
Create Date: 2019-11-06 12:51:38.588756

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '876cd219b280'
down_revision = '0848f178fb1e'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'compliance_sanctions', 'compliance_id', new_column_name='code')


def downgrade():
    op.alter_column(
        'compliance_sanctions', 'code', new_column_name='compliance_id')
