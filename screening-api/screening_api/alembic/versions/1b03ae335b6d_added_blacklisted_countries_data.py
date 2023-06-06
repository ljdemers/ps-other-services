"""Added blacklisted countries data

Revision ID: 1b03ae335b6d
Revises: 49b758ccf60e
Create Date: 2018-03-26 10:20:59.319515

"""
from alembic import op

from screening_api.blacklisted_countries.models import BlacklistedCountry


# revision identifiers, used by Alembic.
revision = '1b03ae335b6d'
down_revision = '49b758ccf60e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.bulk_insert(
        BlacklistedCountry.__table__,
        [
            {
                'country_name': 'Iran',
                'country_id': 'IRN',
                'severity': 'WARNING',
            },
            {
                'country_name': 'Korea, North',
                'country_id': 'KRN',
                'severity': 'CRITICAL',
            },
        ]
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("TRUNCATE TABLE {0}".format(BlacklistedCountry.__tablename__))
    # ### end Alembic commands ###