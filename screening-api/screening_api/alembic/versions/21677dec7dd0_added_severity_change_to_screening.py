"""Added severity_change to screening

Revision ID: 21677dec7dd0
Revises: 4c90f6bdccb4
Create Date: 2017-10-16 13:47:25.018507

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '21677dec7dd0'
down_revision = '4c90f6bdccb4'
branch_labels = None
depends_on = None

severitychange = sa.Enum(
    'DECREASED', 'NOCHANGE', 'INCREASED',
    name='severitychange'
)


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    severitychange.create(op.get_bind())
    op.add_column(
        'screenings',
        sa.Column('severity_change', severitychange, nullable=False),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('screenings', 'severity_change')
    severitychange.drop(op.get_bind(), checkfirst=False)
    # ### end Alembic commands ###
