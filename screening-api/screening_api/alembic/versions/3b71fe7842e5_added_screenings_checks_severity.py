"""Added screenings checks severity

Revision ID: 3b71fe7842e5
Revises: f625e6cdfd0a
Create Date: 2018-08-16 14:10:29.731377

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '3b71fe7842e5'
down_revision = 'f625e6cdfd0a'
branch_labels = None
depends_on = None

severity = postgresql.ENUM(
    'UNKNOWN', 'OK', 'WARNING', 'CRITICAL', name='severity', create_type=False)


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'screenings',
        sa.Column(
            'company_sanctions_severity', severity,
            nullable=False, server_default=sa.text("'UNKNOWN'::severity")),
    )
    op.add_column(
        'screenings',
        sa.Column(
            'country_sanctions_severity', severity,
            nullable=False, server_default=sa.text("'UNKNOWN'::severity")),
    )
    op.add_column(
        'screenings',
        sa.Column(
            'ship_movements_severity', severity,
            nullable=False, server_default=sa.text("'UNKNOWN'::severity")),
    )
    op.add_column(
        'screenings',
        sa.Column(
            'ship_sanctions_severity', severity,
            nullable=False, server_default=sa.text("'UNKNOWN'::severity")),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('screenings', 'ship_sanctions_severity')
    op.drop_column('screenings', 'ship_movements_severity')
    op.drop_column('screenings', 'country_sanctions_severity')
    op.drop_column('screenings', 'company_sanctions_severity')
    # ### end Alembic commands ###
