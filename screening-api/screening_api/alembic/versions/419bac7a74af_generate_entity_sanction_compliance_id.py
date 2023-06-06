"""Generate entity sanction compliance id

Revision ID: 419bac7a74af
Revises: 537a69ee4deb
Create Date: 2018-10-15 12:48:38.235418

"""
from alembic import op
from sqlalchemy.orm import sessionmaker

from screening_api.sanctions.models import ComplianceEntitySanction


# revision identifiers, used by Alembic.
revision = '419bac7a74af'
down_revision = '537a69ee4deb'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    transaction = conn.begin()

    Session = sessionmaker()
    session = Session(bind=conn)

    for i, sanction in enumerate(session.query(ComplianceEntitySanction)):
        sanction.compliance_id = i
        session.add(sanction)

    session.commit()
    session.close()

    transaction.commit()


def downgrade():
    pass
