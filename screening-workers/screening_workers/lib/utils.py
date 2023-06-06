from datetime import datetime
import logging
import structlog

from screening_workers.lib.structlog.processors import SentryProcessor

DATETIME_FORMAT_DEFAULT = "%Y-%m-%dT%H:%M:%SZ"
DATETIME_FORMAT_FALLBACK = "%Y-%m-%dT%H:%M:%S"
DATETIME_FORMAT_FULL = "%Y-%m-%dT%H:%M:%S.%f"
DATE_FORMAT = "%Y-%m-%d"


def str2date(datestr, date_formats=(DATETIME_FORMAT_DEFAULT,
                                    DATETIME_FORMAT_FALLBACK,
                                    DATETIME_FORMAT_FULL,
                                    DATE_FORMAT)):
    # support a single date format arg
    if not type(date_formats) is tuple:
        date_formats = [date_formats]

    for date_format in date_formats:
        try:
            dt = datetime.strptime(datestr, date_format)
        except ValueError:
            pass  # try all formats
        else:
            return dt.replace(tzinfo=None)

    raise ValueError(f'{datestr} does not match any date format')


def date2str(date, date_format=DATETIME_FORMAT_DEFAULT):
    return datetime.strftime(date, date_format)


def json_logger(name, level=None, indent=None):
    processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt='iso'),
            SentryProcessor(),
            structlog.processors.JSONRenderer(indent=indent,
                                              sort_keys=True),
    ]

    base_logger = logging.getLogger(name)

    if level:
        base_logger.setLevel(level)

    return structlog.wrap_logger(base_logger, processors=processors)
