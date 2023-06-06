"""Calculated screenings checks severity

Revision ID: c9fbb9be81b4
Revises: 3b71fe7842e5
Create Date: 2018-08-16 14:16:04.982469

"""
from alembic import op
from sqlalchemy.orm import sessionmaker

from screening_api.screenings.models import Screening


# revision identifiers, used by Alembic.
revision = 'c9fbb9be81b4'
down_revision = '3b71fe7842e5'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    transaction = conn.begin()

    Session = sessionmaker()
    session = Session(bind=conn)

    for screening in session.query(Screening):
        screening.company_sanctions_severity =\
            screening.calculated_company_sanctions_severity
        screening.country_sanctions_severity =\
            screening.calculated_country_sanctions_severity
        screening.ship_movements_severity =\
            screening.calculated_ship_movements_severity
        screening.ship_sanctions_severity =\
            screening.calculated_ship_sanctions_severity
        session.add(screening)

    session.commit()
    session.close()

    transaction.commit()


def downgrade():
    pass
