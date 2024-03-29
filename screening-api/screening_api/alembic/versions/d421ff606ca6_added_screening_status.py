"""Added screening status

Revision ID: d421ff606ca6
Revises: 05c51c099250
Create Date: 2017-12-14 12:04:24.009821

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd421ff606ca6'
down_revision = '05c51c099250'
branch_labels = None
depends_on = None

status = sa.Enum('CREATED', 'SCHEDULED', 'PENDING', 'DONE', name='status')


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    status.create(op.get_bind())
    op.add_column(
        'screenings',
        sa.Column(
            'status', status,
            nullable=False,
            server_default='DONE',
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('screenings', 'status')
    status.drop(op.get_bind(), checkfirst=False)
    # ### end Alembic commands ###
