import time
import datetime
from collections import namedtuple

from geoalchemy2 import Geometry
from sqlalchemy import func
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import as_declarative

from api_clients.utils import json_logger, json_unzip, ZIPJSON_KEY
from smh_service.smh_config import db

from ps_env_config import config

logger = json_logger(__name__, level=config.get('LOG_LEVEL'), sort_keys=False)


@as_declarative()
class Base:
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)


class SMHUsers(Base):
    __tablename__ = 'smh_users'
    last_login = db.Column(db.DateTime(timezone=True),
                           onupdate=datetime.datetime.utcnow)
    username = db.Column(db.String(25))
    password = db.Column(db.String(25))
    request_count = db.Column(db.Integer)

    @classmethod
    def update_user_request_count(cls, username):
        user = db.session.query(cls).filter_by(username=username).one()
        user.request_count += 1
        db.session.commit()


class SMHData(Base):
    __tablename__ = 'smh_data'
    timestamp = db.Column(db.DateTime())
    imo_number = db.Column(db.String(10))
    cached_days = db.Column(db.Integer)
    options = db.Column(postgresql.JSONB)
    port_visits = db.Column(postgresql.JSONB, nullable=False)
    positions = db.Column(postgresql.JSONB, nullable=False)
    ihs_movements = db.Column(postgresql.JSONB, nullable=False)
    ais_gaps = db.Column(postgresql.JSONB)
    eez_visits = db.Column(postgresql.JSONB)
    misc_data = db.Column(postgresql.JSONB)
    update_count = db.Column(db.Integer, default=0)

    # update from dict
    def update(self, data_dict):
        for key, value in data_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def get_cached_smh_data(cls, imo_number, offset):

        # unzip if needed otherwise return item as is
        def get_unzip_data(item):
            if item and isinstance(item, list) and ZIPJSON_KEY in item[0]:
                return json_unzip(item[0])
            elif item and ZIPJSON_KEY in item:
                return json_unzip(item)
            return item

        start_time = time.monotonic()
        cached_data = namedtuple('cached_data', ['options', 'port_visits', 'positions',
                                                 'ihs_data', 'gap_data', 'eez_visits'])
        cached_smh = db.session.query(cls).filter_by(imo_number=imo_number). \
            order_by(cls.timestamp.desc()).offset(offset).limit(1).one_or_none()

        elapsed = round(time.monotonic() - start_time, 3)
        try:
            if cached_smh:
                logger.debug(cached_smh=(cached_smh.id, cached_smh.timestamp, offset, elapsed))
                cached_smh.options['read_db_elapsed'] = elapsed
                cached_smh.options['update_count'] = cached_smh.update_count or 0
                cached_smh.options['timestamp'] = cached_smh.timestamp
                cached_smh.options['id'] = str(cached_smh._id) if hasattr(cached_smh, '_id') \
                    else cached_smh.id

                # unzip position, ihs, and gap data if required
                position_data = get_unzip_data(cached_smh.positions or {})
                ihs_data = get_unzip_data(cached_smh.ihs_movements or [])
                gap_data = get_unzip_data(cached_smh.ais_gaps or [])

                return cached_data(cached_smh.options,
                                   cached_smh.port_visits or {},
                                   position_data, ihs_data,
                                   gap_data, cached_smh.eez_visits or []
                                   )
        except Exception as exc:
            logger.warning('DB read exception', exc=exc)

        return cached_data({}, {}, {}, [], [], [])

    def insert_update_smh_data(self, data, last_id=None, overwrite=True):
        imo_number = data.get("imo_number")
        options = data.get("options")

        data['update_count'] = options.get('last_update_count', 0) + 1
        logger.info("Saving to DB.",
                    last_id=last_id, imo_number=imo_number,
                    smh_timestamp=data['timestamp'],
                    update=data['update_count']
                    )

        if last_id and overwrite:
            smh_data = db.session.query(SMHData).get(last_id)
            data['id'] = last_id
            smh_data.update(data)
            logger.debug('DB updated', id=last_id)
        else:
            smh_data = SMHData(**data)
            db.session.add(smh_data)
        db.session.commit()


class Regions(Base):
    __tablename__ = 'regions'
    code = db.Column(db.String(8), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    polygon = db.Column(Geometry('POLYGON'))
    source = db.Column(db.String(32))
    country_code_id = db.Column(db.String(3))
    mrg_id = db.Column(db.Integer, nullable=False)
    _type = db.Column('type', db.String(128))
    status = db.Column(db.SmallInteger, nullable=False, default=1)


@as_declarative()
class EezBase:
    mrg_id = db.Column(db.Integer, primary_key=True)
    eez_code = db.Column(db.String(8), nullable=False)
    eez_name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    eez_polygon = db.Column(Geometry('POLYGON'))
    eez_source = db.Column(db.String(32))
    country_code_id = db.Column(db.String(3))
    _type = db.Column('type', db.String(128))
    status = db.Column(db.SmallInteger, nullable=False, default=1)


class Eez_12nm(EezBase):
    __tablename__ = 'eez_12nm'


class Eez_200nm(EezBase):
    __tablename__ = 'eez_200nm'


class PortVisits(Base):
    __tablename__ = 'portVisits'
    portcall_id = db.Column(db.Integer)
    data_rate = db.Column(db.Integer)
    visit_type = db.Column(db.String(50))
    imo_number = db.Column(db.String(7), nullable=False)
    mmsi = db.Column(db.String(9))
    entered = db.Column(db.DateTime, nullable=False)
    departed = db.Column(db.DateTime)
    # Should use the earthdistance module instead
    # https://www.postgresql.org/docs/9.1/earthdistance.html
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    speed = db.Column(db.Float)
    heading = db.Column(db.Float)
    port_code = db.Column(db.String(25))
    ihs_port_name = db.Column(db.String(100))


# depreciated
class PortCalls(Base):
    __tablename__ = 'portcalls'
    timestamp = db.Column(db.DateTime(timezone=True))
    imo_number = db.Column(db.String(10))
    port_calls = db.Column(postgresql.JSON, nullable=False)
    options = db.Column(postgresql.JSON)


def get_eez(positions, table='eez_200nm', field_prefix='eez_', status='1',
            session=db.session):
    """
       Perform the EEZ or region detection for each position.
       Assuming that the EEZ table exist in the SMH DB.

       Args:
           positions (list): Position list to find if within an EEZ
           table (str): eez_200nm is default or eez_12nm or any other compatible/populated table
           field_prefix (str): eez_ is default
           status (str): comma-separated list, default = '1'
           session: DB session

       Returns:
           A list of EEZ/region Visits dict
    """
    not_found = {"port_code": "0", "port_name": "", "port_country_name": ""}
    models = {"eez_200nm": Eez_200nm, "eez_12nm": Eez_12nm, "regions": Regions}
    model = models.get(table)
    polygon = getattr(model, f"{field_prefix}polygon")

    for pos in positions:
        if not model or pos.get("latitude") is None or pos.get("longitude") is None:
            yield not_found
            continue

        point = f"""POINT({pos["longitude"]} {pos["latitude"]})"""
        result = session.query(getattr(model, f"{field_prefix}name").label("port_name"),
                               getattr(model, f"{field_prefix}code").label("port_code"),
                               getattr(model, "mrg_id").label("port_id"),
                               getattr(model, "country_code_id").label("port_country_name"),
                               getattr(model, "_type").label("region_type"),
                               getattr(model, "latitude").label("port_latitude"),
                               getattr(model, "longitude").label("port_longitude")) \
            .filter(model.status.in_(status.split(","))) \
            .filter(func.ST_Contains(polygon,  point)).one_or_none()

        yield dict(zip(result.keys(), result)) if result else not_found

