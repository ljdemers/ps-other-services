from __future__ import with_statement
from logging.config import fileConfig
import os
from urllib.parse import urlunparse

from alembic import context
from sqlalchemy import pool, create_engine
from ujson import dumps, loads

from screening_api.models import BaseModel
from screening_api.blacklisted_countries.models import BlacklistedCountry
from screening_api.blacklisted_sanctions.models import (
    BlacklistedSanctionListItem, BlacklistedSanctionList,
)
from screening_api.companies.models import (
    SISComplianceAssociation, SISCompany,
)
from screening_api.company_associations.models import CompanyAssociation
from screening_api.entities.models import ComplianceEntity
from screening_api.sanctions.models import (
    ComplianceSanction, ComplianceEntitySanction,
)
from screening_api.ships.models import Ship
from screening_api.ship_inspections.models import ShipInspection
from screening_api.ship_sanctions.models import ShipSanction
from screening_api.screenings.models import Screening
from screening_api.screenings_bulk.models import BulkScreening
from screening_api.screenings_history.models import ScreeningHistory
from screening_api.screenings_reports.models import ScreeningReport

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
assert CompanyAssociation
assert BlacklistedCountry
assert BlacklistedSanctionListItem
assert BlacklistedSanctionList
assert SISComplianceAssociation
assert SISCompany
assert ComplianceEntity
assert ComplianceEntitySanction
assert ComplianceSanction
assert Ship
assert ShipInspection
assert ShipSanction
assert Screening
assert BulkScreening
assert ScreeningHistory
assert ScreeningReport
target_metadata = BaseModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    netloc = '{0}:{1}@{2}:{3}'.format(
        os.environ['DBUSER'],
        os.environ['DBPASSWORD'],
        os.environ['DBHOST'],
        '5432',
    )
    dbname = os.environ['DBNAME']
    return urlunparse(
        ('postgresql+psycopg2', netloc, dbname, None, None, None),
    )


def get_connectable(url):
    options = {
        'poolclass': pool.NullPool,
        '_coerce_config': True,
        'json_serializer': dumps,
        'json_deserializer': loads,
    }
    return create_engine(url, **options)


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = get_url()
    connectable = get_connectable(url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
