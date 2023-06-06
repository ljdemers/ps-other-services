"""Updated blacklisted countries data

Revision ID: 0848f178fb1e
Revises: dd80acd1b0ae
Create Date: 2019-11-01 12:05:08.577284

"""
from alembic import op

from screening_api.blacklisted_countries.models import BlacklistedCountry


# revision identifiers, used by Alembic.
revision = '0848f178fb1e'
down_revision = 'dd80acd1b0ae'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("TRUNCATE TABLE {0}".format(BlacklistedCountry.__tablename__))
    op.bulk_insert(
        BlacklistedCountry.__table__,
        [
            {
                'country_name': 'Korea, North',
                'country_id': 'KRN',
                'severity': 'CRITICAL',
            },
            {
                'country_name': 'Iran',
                'country_id': 'IRN',
                'severity': 'CRITICAL',
            },
            {
                'country_name': 'Cuba',
                'country_id': 'CUB',
                'severity': 'CRITICAL',
            },
            {
                'country_name': 'Syrian Arab Republic',
                'country_id': 'SYR',
                'severity': 'CRITICAL',
            },
        ]
    )


def downgrade():
    op.execute("TRUNCATE TABLE {0}".format(BlacklistedCountry.__tablename__))
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
