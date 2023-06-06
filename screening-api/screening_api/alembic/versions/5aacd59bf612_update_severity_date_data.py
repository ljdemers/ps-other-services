"""Update severity date data

Revision ID: 5aacd59bf612
Revises: 4228b731adad
Create Date: 2018-07-26 13:46:41.935883

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5aacd59bf612'
down_revision = '4228b731adad'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    screenings_history_table = sa.Table(
        'screenings_history', sa.MetaData(bind=conn), autoload=True)
    conn.execute(
        screenings_history_table.update().values(
            severity_date=screenings_history_table.c.created
        ).where(
            screenings_history_table.c.severity_date.is_(None),
        )
    )


def downgrade():
    pass
