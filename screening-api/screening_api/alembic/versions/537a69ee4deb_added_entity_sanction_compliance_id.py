"""Added entity sanction compliance id

Revision ID: 537a69ee4deb
Revises: ee7a64f57058
Create Date: 2018-10-15 12:42:53.763172

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '537a69ee4deb'
down_revision = 'ee7a64f57058'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'compliance_entity_sanctions',
        sa.Column('compliance_id', sa.Integer(), nullable=True),
    )
    op.create_unique_constraint(
        'compliance_entity_sanctions_compliance_id_unique',
        'compliance_entity_sanctions', ['compliance_id'],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        'compliance_entity_sanctions_compliance_id_unique',
        'compliance_entity_sanctions', type_='unique',
    )
    op.drop_column('compliance_entity_sanctions', 'compliance_id')
    # ### end Alembic commands ###