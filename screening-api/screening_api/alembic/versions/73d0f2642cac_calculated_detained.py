"""Calculated detained

Revision ID: 73d0f2642cac
Revises: e4c47d85e8e5
Create Date: 2019-10-02 10:04:54.897002

"""
from alembic import op
from sqlalchemy.orm import sessionmaker

from screening_api.ship_inspections.models import ShipInspection


# revision identifiers, used by Alembic.
revision = '73d0f2642cac'
down_revision = 'e4c47d85e8e5'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    transaction = conn.begin()

    Session = sessionmaker()
    session = Session(bind=conn)

    for inspection in session.query(ShipInspection):
        inspection.detained = inspection.calculated_detained
        session.add(inspection)

    session.commit()
    session.close()

    transaction.commit()


def downgrade():
    pass
