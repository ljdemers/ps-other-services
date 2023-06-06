from datetime import datetime, timezone
import logging
import structlog
from functools import wraps

import zlib
import orjson as json
import base64


ZIPJSON_KEY = 'base64(zip(o))'

DATETIME_FORMAT_DEFAULT = "%Y-%m-%dT%H:%M:%SZ"
DATETIME_FORMAT_FALLBACK = "%Y-%m-%dT%H:%M:%S"
DATETIME_FORMAT_FALLBACK2 = "%Y-%m-%d %H:%M:%S"
DATETIME_FORMAT_FULL = "%Y-%m-%dT%H:%M:%S.%f"
DATE_FORMAT = "%Y-%m-%d"


def str2date(datestr, tz_aware=False, date_formats=(DATETIME_FORMAT_DEFAULT,
                                                    DATETIME_FORMAT_FALLBACK,
                                                    DATETIME_FORMAT_FALLBACK2,
                                                    DATETIME_FORMAT_FULL,
                                                    DATE_FORMAT)):
    # support a single date format arg
    if not isinstance(date_formats, tuple):
        date_formats = [date_formats]

    for date_format in date_formats:
        try:
            dt = datetime.strptime(datestr, date_format)
            if tz_aware:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.replace(tzinfo=None)
            return dt
        except (ValueError, TypeError):
            pass  # try all formats

    return None


def date2str(date, date_format=DATETIME_FORMAT_DEFAULT):
    return datetime.strftime(date, date_format)


def json_logger(name, level=None, indent=None, sort_keys=True):
    processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.processors.JSONRenderer(indent=indent,
                                              sort_keys=sort_keys),
    ]

    base_logger = logging.getLogger(name)

    if level:
        base_logger.setLevel(level)

    return structlog.wrap_logger(base_logger, processors=processors)


def convert_float(value):
    float_value = value
    try:
        if value:
            float_value = float(value)
    except:
        pass

    return float_value


def memoized(func):
    """
    Decorator for memoizing the return value from a function. This allows for
    easy lazy-evaluating logic. The first time the decorated function is
    called, the result is calculated and stored. Upon later use, the stored
    result is returned.

    Args:
        func: The function to be called the first time.

    Returns:
        The result from the first call to this function.
    """
    @wraps(func)
    def check_result():
        """ Check if there is a previous result. If not,
        calculate and store it for later use. """
        if not hasattr(func, 'result'):
            func.result = func()
        return func.result

    # make the func (and result) accessible to test code
    check_result.func = func

    return check_result


def json_zip(j):

    j = {
        ZIPJSON_KEY: base64.b64encode(
            zlib.compress(
                json.dumps(j)  # .encode('utf-8')
            )
        ).decode('ascii')
    }

    return j


def json_unzip(j, insist=True):
    try:
        assert (j.get(ZIPJSON_KEY))
        assert (set(j.keys()) == {ZIPJSON_KEY})
    except:
        if insist:
            raise RuntimeError("JSON not in the expected format {" +
                               str(ZIPJSON_KEY) + ": zipstring}")
        else:
            return j

    try:
        j = zlib.decompress(base64.b64decode(j[ZIPJSON_KEY]))
    except:
        raise RuntimeError("Could not decode/unzip the contents")

    try:
        j = json.loads(j)
    except:
        raise RuntimeError("Could interpret the unzipped contents")

    return j
