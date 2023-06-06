"""Added imo field for ships

Revision ID: 384e96d65cad
Revises: 21677dec7dd0
Create Date: 2017-10-19 13:33:42.279282

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '384e96d65cad'
down_revision = '21677dec7dd0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ships', sa.Column('imo', sa.String(), nullable=False))
    op.create_unique_constraint(None, 'ships', ['imo'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'ships', type_='unique')
    op.drop_column('ships', 'imo')
    # ### end Alembic commands ###
