"""Added company codes

Revision ID: b3ceee7863fd
Revises: b16e052afa9c
Create Date: 2018-04-30 10:35:18.024432

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3ceee7863fd'
down_revision = 'b16e052afa9c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'ships',
        sa.Column(
            'group_beneficial_owner_company_code', sa.String(), nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'group_beneficial_owner_company_id', sa.Integer(), nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'operator_company_code', sa.String(), nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'operator_company_id', sa.Integer(), nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'registered_owner_company_code', sa.String(), nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'registered_owner_company_id', sa.Integer(), nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'ship_manager_company_code', sa.String(), nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'ship_manager_company_id', sa.Integer(), nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'technical_manager_company_code', sa.String(), nullable=True,
        ),
    )
    op.add_column(
        'ships',
        sa.Column(
            'technical_manager_company_id', sa.Integer(), nullable=True,
        ),
    )
    op.create_foreign_key(
        'ships_operator_company_id_fkey', 'ships', 'sis_companies',
        ['operator_company_id'], ['id'],
        onupdate='CASCADE', ondelete='CASCADE',
    )
    op.create_foreign_key(
        'ships_technical_manager_company_id_fkey', 'ships', 'sis_companies',
        ['technical_manager_company_id'], ['id'],
        onupdate='CASCADE', ondelete='CASCADE',
    )
    op.create_foreign_key(
        'ships_group_beneficial_owner_company_id_fkey', 'ships',
        'sis_companies', ['group_beneficial_owner_company_id'], ['id'],
        onupdate='CASCADE', ondelete='CASCADE',
    )
    op.create_foreign_key(
        'ships_ship_manager_company_id_fkey', 'ships', 'sis_companies',
        ['ship_manager_company_id'], ['id'],
        onupdate='CASCADE', ondelete='CASCADE',
    )
    op.create_foreign_key(
        'ships_registered_owner_company_id_fkey', 'ships', 'sis_companies',
        ['registered_owner_company_id'], ['id'],
        onupdate='CASCADE', ondelete='CASCADE',
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        'ships_registered_owner_company_id_fkey', 'ships', type_='foreignkey')
    op.drop_constraint(
        'ships_ship_manager_company_id_fkey', 'ships', type_='foreignkey')
    op.drop_constraint(
        'ships_group_beneficial_owner_company_id_fkey', 'ships',
        type_='foreignkey',
    )
    op.drop_constraint(
        'ships_technical_manager_company_id_fkey', 'ships', type_='foreignkey')
    op.drop_constraint(
        'ships_operator_company_id_fkey', 'ships', type_='foreignkey',
    )
    op.drop_column('ships', 'technical_manager_company_id')
    op.drop_column('ships', 'technical_manager_company_code')
    op.drop_column('ships', 'ship_manager_company_id')
    op.drop_column('ships', 'ship_manager_company_code')
    op.drop_column('ships', 'registered_owner_company_id')
    op.drop_column('ships', 'registered_owner_company_code')
    op.drop_column('ships', 'operator_company_id')
    op.drop_column('ships', 'operator_company_code')
    op.drop_column('ships', 'group_beneficial_owner_company_id')
    op.drop_column('ships', 'group_beneficial_owner_company_code')
    # ### end Alembic commands ###
