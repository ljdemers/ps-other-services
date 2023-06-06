"""Update ship info

Revision ID: c2ac076fd1a5
Revises: 41ee2bc07eef
Create Date: 2018-11-20 14:30:37.262482

"""
from itertools import chain, islice

from alembic import op
from sqlalchemy.orm import sessionmaker, joinedload

from screening_api.screenings_reports.models import ScreeningReport
from screening_api.screenings_history.models import ScreeningHistory


# revision identifiers, used by Alembic.
revision = 'c2ac076fd1a5'
down_revision = '41ee2bc07eef'
branch_labels = None
depends_on = None


def create_ship_info(ship):
    return {
        'name': ship.name,
        'imo': ship.imo,
        'type': ship.type,
        'build_year': int(ship.build_year),
        'build_age': int(ship.build_age),
        'build_age_severity': ship.build_age_severity.name,
        'country_name': ship.country_name,
        'country_id': ship.country_id,
        'flag_effective_date': ship.flag_effective_date,
        'mmsi': ship.mmsi,
        'call_sign': ship.call_sign,
        'status': ship.status,
        'port_of_registry': ship.port_of_registry,
        'deadweight': int(ship.deadweight),
        'weight': int(ship.weight),
        'length': ship.length,
        'breadth': ship.breadth,
        'displacement': int(ship.displacement),
        'draught': ship.draught,
        'registered_owner': ship.registered_owner,
        'operator': ship.operator,
        'group_beneficial_owner': ship.group_beneficial_owner,
        'ship_manager': ship.ship_manager,
        'technical_manager': ship.technical_manager,
        'shipbuilder': ship.shipbuilder,
        'build_country_name': ship.build_country_name,
        'classification_society': ship.classification_society,
    }


def _batch_iter(n, iterable):
    it = iter(iterable)
    while True:
        batch = list(islice(it, n))
        if not batch:
            return
        yield from batch


def upgrade():
    conn = op.get_bind()

    Session = sessionmaker()
    session = Session(bind=conn)

    batchsize = 200
    reports = session.query(ScreeningReport).options(
        joinedload('screening.ship', innerjoin=True)).yield_per(batchsize)
    history = session.query(ScreeningHistory).options(
        joinedload('screening.ship', innerjoin=True)).yield_per(batchsize)

    reports_iter = _batch_iter(batchsize, reports)
    history_iter = _batch_iter(batchsize, history)
    for instance in chain(reports_iter, history_iter):
        instance.ship_info = create_ship_info(instance.screening.ship)
        session.add(instance)

    session.commit()
    session.close()


def downgrade():
    pass
