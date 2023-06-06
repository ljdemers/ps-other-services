from datetime import date, datetime
from enum import Enum
import logging

from dateutil.tz import tzutc
from flask import json
from sqlalchemy.ext.declarative import DeclarativeMeta

log = logging.getLogger(__name__)

UTC = tzutc()


class AlchemyEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, (datetime, date)):
            if o.tzinfo:
                o = o.astimezone(UTC).replace(tzinfo=None)
            return o.isoformat() + 'Z'
        if isinstance(o, Enum):
            return o.name
        if isinstance(o.__class__, DeclarativeMeta):
            data = {}
            fields = o.__json__() if hasattr(o, '__json__') else dir(o)
            restricted_fields = ['metadata', 'query', 'query_class']
            object_fields = [
                f for f in fields
                if not f.startswith('_') and f not in restricted_fields
            ]
            for field in object_fields:
                value = o.__getattribute__(field)
                try:
                    json.dumps(value)
                    data[field] = value
                except TypeError as exc:
                    log.warning(str(exc))
                    data[field] = None
            return data
        return super(AlchemyEncoder, self).default(o)
