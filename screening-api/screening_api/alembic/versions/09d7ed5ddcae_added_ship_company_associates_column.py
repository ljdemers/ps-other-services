"""Added ship company associates column

Revision ID: 09d7ed5ddcae
Revises: 7b8ffa761138
Create Date: 2018-05-02 09:11:21.478313

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '09d7ed5ddcae'
down_revision = '7b8ffa761138'
branch_labels = None
depends_on = None


status = postgresql.ENUM(
    'CREATED', 'DONE', 'SCHEDULED', 'PENDING', name='status',
    create_type=False,
)
severity = postgresql.ENUM(
    'OK', 'WARNING', 'CRITICAL', 'UNKNOWN', name='severity', create_type=False)


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'screenings',
        sa.Column(
            'ship_company_associates_severity', severity,
            nullable=False, server_default=sa.text("'UNKNOWN'::severity"),
        ),
    )
    op.add_column(
        'screenings',
        sa.Column(
            'ship_company_associates_status', status,
            nullable=False, server_default=sa.text("'CREATED'::status"),
        ),
    )
    op.add_column(
        'screenings_history',
        sa.Column(
            'ship_company_associates_severity', severity,
            nullable=False, server_default=sa.text("'UNKNOWN'::severity"),
        ),
    )
    op.add_column(
        'screenings_reports',
        sa.Column('ship_company_associates', sa.JSON(), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('screenings_reports', 'ship_company_associates')
    op.drop_column('screenings_history', 'ship_company_associates_severity')
    op.drop_column('screenings', 'ship_company_associates_status')
    op.drop_column('screenings', 'ship_company_associates_severity')
    # ### end Alembic commands ###
