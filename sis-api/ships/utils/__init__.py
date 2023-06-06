import datetime as dt
import logging
import os
from collections import deque
from contextlib import contextmanager
from functools import wraps
from time import time
from typing import Any, Iterable, Optional, Text, Union

from django.conf import settings
from django.core.management.color import color_style
from django_celery_beat.utils import make_aware

from ships.constants import (YEAR_FORMAT, YEAR_LEN, YEAR_MONTH_FORMAT,
                             YEAR_MONTH_LEN)

logger = logging.getLogger(__name__)
style = color_style()


def get_first(iterable: Iterable, default: Any = None) -> Any:
    """Gets the first item from an itrerable.

    >>> get_first([1])
    1

    >>> get_first([], default=True)
    True

    """

    return next(iter(iterable), default)


def get_last(iterable: Iterable, default: Any = None) -> Any:
    """Gets the last item from an itrerable.

    >>> get_last([1, 2])
    2

    >>> get_last([], default=True)
    True

    """

    try:
        return deque(iter(iterable), maxlen=1).pop()
    except IndexError:
        return default


def validate_int_field(value: Optional[Union[str, int]]) -> Union[str, int, None]:
    """Validates if int is not an empty string.

    >>> validate_int_field('')


    >>> validate_int_field('5')
    '5'

    >>> validate_int_field(5)
    5

    """

    return value if value != '' else None


def convert_file_timestamp(timestamp: str) -> dt.datetime:
    """Converts a file timestamp into Python datetime object and attaches UTC
    timezone.

    >>> convert_file_timestamp('/opt/data/201812140603_ShipData.CSV')
    datetime.datetime(2018, 12, 14, 6, 3, tzinfo=datetime.timezone.utc)

    >>> convert_file_timestamp('201812140603_ShipData.CSV')
    datetime.datetime(2018, 12, 14, 6, 3, tzinfo=datetime.timezone.utc)

    >>> convert_file_timestamp('/opt/data/201812140603')
    datetime.datetime(2018, 12, 14, 6, 3, tzinfo=datetime.timezone.utc)


    """

    timestamp = get_last(timestamp.split('/'))
    timestamp = get_first(timestamp.split('_'))

    try:
        datetime = dt.datetime.strptime(timestamp, '%Y%m%d%H%M')
    except ValueError:
        datetime = dt.datetime.strptime(timestamp, '%Y%m%d')

    return datetime.replace(tzinfo=dt.timezone.utc)


def time_it(func):
    """Gives an execution time of a given function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time()
        f = func(*args, **kwargs)
        end = time()

        logger.info(style.WARNING('Took time: {:.5f}'.format(end - start)))
        return f

    return wrapper


def str2date(date: str, default: Optional[dt.datetime] = None) -> Optional[dt.datetime]:
    """Converts string into datetime object.

    Flag effective date has ``YYYYMM`` format, but there are cases when
    its value may be ``199000`` for example. For such cases we strip months
    information and parse year only.

    Args:
        date (str): flag effective date string.
        default (datetime): value to set if date is empty
            or has an invalid form.

    Returns:
        datetime: parsed datetime object or ``default`` if parsing failed.
    """
    if not date:
        return default

    return (
        parse_date(date[:YEAR_MONTH_LEN], YEAR_MONTH_FORMAT)
        or parse_date(date[:YEAR_LEN], YEAR_FORMAT)
        or default
    )


def parse_date(date: str, patt: str) -> Optional[dt.datetime]:
    try:
        return make_aware(dt.datetime.strptime(date, patt))
    except ValueError:
        return


@contextmanager
def log_execution(filename_prefix: Text):
    """Create log file with a timestamp.

    Context manager that creates log file with a timestamp in
    its name. Useful to store logs separately for each execution.

    Args:
         filename_prefix: file name prefix.
    """
    is_file_logging_enabled = os.path.exists(settings.LOG_FILE_PATH)

    if is_file_logging_enabled:
        filename = os.path.join(
            settings.LOG_FILE_PATH,
            f'{filename_prefix}_{dt.datetime.now():%Y%m%dT%H%M%S}.log',
        )
        fh = logging.FileHandler(filename, mode='w+')

        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(formatter)

        logger_ = logging.getLogger('management')
        logger_.addHandler(fh)

    try:
        yield
    finally:
        if is_file_logging_enabled:
            logger_.removeHandler(fh)
