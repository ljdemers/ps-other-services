"""Previous severity nullable

Revision ID: 7f2db642004d
Revises: abac0389a3da
Create Date: 2018-05-25 09:25:27.534996

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f2db642004d'
down_revision = 'abac0389a3da'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        'screenings', 'previous_severity',
        nullable=True, server_default=None,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        'screenings', 'previous_severity',
        nullable=False, server_default=sa.text("'UNKNOWN'::severity"),
    )
    # ### end Alembic commands ###