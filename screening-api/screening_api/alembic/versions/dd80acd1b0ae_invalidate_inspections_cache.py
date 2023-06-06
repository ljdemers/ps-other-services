"""Invalidate inspections cache

Revision ID: dd80acd1b0ae
Revises: 73d0f2642cac
Create Date: 2019-10-07 13:57:01.106158

"""
from alembic import op
from sqlalchemy.orm import sessionmaker

from screening_api.ship_inspections.models import ShipInspection


# revision identifiers, used by Alembic.
revision = 'dd80acd1b0ae'
down_revision = '73d0f2642cac'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    transaction = conn.begin()

    Session = sessionmaker()
    session = Session(bind=conn)

    session.query(ShipInspection).delete()

    session.commit()
    session.close()

    transaction.commit()


def downgrade():
    pass
