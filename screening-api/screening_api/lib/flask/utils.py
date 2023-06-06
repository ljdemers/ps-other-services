from datetime import datetime


DATETIME_FORMAT_DEFAULT = "%Y-%m-%dT%H:%M:%SZ"
DATETIME_FORMAT_FALLBACK = "%Y-%m-%dT%H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


def str2date(datestr, date_formats=(DATETIME_FORMAT_DEFAULT,
                                    DATETIME_FORMAT_FALLBACK,
                                    DATE_FORMAT)):
    # support a single date format arg
    if not type(date_formats) is tuple:
        date_formats = [date_formats]

    for date_format in date_formats:
        try:
            return datetime.strptime(datestr, date_format)
        except ValueError:
            pass  # try all formats

    return None


def date2str(date, date_format=DATETIME_FORMAT_DEFAULT):
    return datetime.strftime(date, date_format)


def format_severity(severity):
    cls = ""
    if severity == 'CRITICAL':
        cls = "severity-text-critical"
    elif severity == 'WARNING':
        cls = "severity-text-warning"
    return cls


def format_title_severity(severity):
    cls = ""
    if severity == 'CRITICAL':
        cls = "severity-text-critical"
    elif severity == 'WARNING':
        cls = "severity-text-warning"
    elif severity == 'OK':
        cls = "severity-text-ok"
    return cls


def format_border_severity(severity):
    cls = ""
    if severity == 'CRITICAL':
        cls = "severity-border-critical"
    elif severity == 'WARNING':
        cls = "severity-border-warning"
    elif severity == 'OK':
        cls = "severity-border-ok"
    return cls


def format_datetime(value):
    dt = "-"
    try:
        dt = datetime.strftime(str2date(value), '%d %b %Y %H:%M')
    except:
        pass
    return dt


def format_date(value, default="Current"):
    dt = default
    try:
        dt = datetime.strftime(str2date(value), '%d %b %Y')
    except:
        pass
    return dt
