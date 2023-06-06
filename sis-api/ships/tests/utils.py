import datetime

from typing import Union

def serialize_datetime(d: datetime) -> Union[str, None]:
    if not d:
        return

    if d.tzinfo and d.tzinfo.utcoffset(d):
        d.replace(tzinfo=datetime.timezone.utc)

    return d.strftime('%Y-%m-%dT%H:%M:%S.%f')
