"""Added ship companies

Revision ID: 063384afd599
Revises: 2220acf0794d
Create Date: 2018-04-06 13:28:03.663157

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '063384afd599'
down_revision = '2220acf0794d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'ships',
        sa.Column('group_beneficial_owner', sa.String(), nullable=True),
    )
    op.add_column(
        'ships',
        sa.Column('operator', sa.String(), nullable=True),
    )
    op.add_column(
        'ships',
        sa.Column('registered_owner', sa.String(), nullable=True),
    )
    op.add_column(
        'ships',
        sa.Column('ship_manager', sa.String(), nullable=True),
    )
    op.add_column(
        'ships',
        sa.Column('technical_manager', sa.String(), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ships', 'technical_manager')
    op.drop_column('ships', 'ship_manager')
    op.drop_column('ships', 'registered_owner')
    op.drop_column('ships', 'operator')
    op.drop_column('ships', 'group_beneficial_owner')
    # ### end Alembic commands ###