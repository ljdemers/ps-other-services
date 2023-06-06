"""Added ship countries

Revision ID: fbcd7c95575f
Revises: 1b03ae335b6d
Create Date: 2018-03-26 15:30:38.102404

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fbcd7c95575f'
down_revision = '1b03ae335b6d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'ships',
        sa.Column(
            'group_beneficial_owner_country_of_control', sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'group_beneficial_owner_country_of_domicile', sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'group_beneficial_owner_country_of_registration', sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'operator_country_of_control', sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'operator_country_of_domicile_name', sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'operator_country_of_registration', sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'registered_owner_country_of_control', sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'registered_owner_country_of_domicile', sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'registered_owner_country_of_registration', sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'ship_manager_country_of_control', sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'ship_manager_country_of_domicile_name', sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'ship_manager_country_of_registration', sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'technical_manager_country_of_control', sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'technical_manager_country_of_domicile', sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'technical_manager_country_of_registration', sa.String(),
            nullable=True,
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ships', 'technical_manager_country_of_registration')
    op.drop_column('ships', 'technical_manager_country_of_domicile')
    op.drop_column('ships', 'technical_manager_country_of_control')
    op.drop_column('ships', 'ship_manager_country_of_registration')
    op.drop_column('ships', 'ship_manager_country_of_domicile_name')
    op.drop_column('ships', 'ship_manager_country_of_control')
    op.drop_column('ships', 'registered_owner_country_of_registration')
    op.drop_column('ships', 'registered_owner_country_of_domicile')
    op.drop_column('ships', 'registered_owner_country_of_control')
    op.drop_column('ships', 'operator_country_of_registration')
    op.drop_column('ships', 'operator_country_of_domicile_name')
    op.drop_column('ships', 'operator_country_of_control')
    op.drop_column('ships', 'group_beneficial_owner_country_of_registration')
    op.drop_column('ships', 'group_beneficial_owner_country_of_domicile')
    op.drop_column('ships', 'group_beneficial_owner_country_of_control')
    # ### end Alembic commands ###
