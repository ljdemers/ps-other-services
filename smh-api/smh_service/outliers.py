from geopy.distance import great_circle

from api_clients.utils import str2date, json_logger
from ps_env_config import config

logger = json_logger(__name__, level=config.get('LOG_LEVEL'))
MAX_SPEED = 100


def is_position_an_outlier(position: dict, last_position: dict):
    """
    Calculate the speed difference from this and the last position. If
    the calculated_speed is more than the reported / calculated Speed or
    if this position Speed is more than the MAX_SPEED return True as this
    position is an outlier
    Returns:
         bool: True if outlier. False if not an outlier.
    """

    if (
            (not -90 <= position['latitude'] <= 90) or
            (not -180 <= position['longitude'] <= 180)
    ):
        return True

    if last_position:
        position_timestamp = str2date(position.get('timestamp'))
        try:
            last_position_timestamp = \
                    str2date(last_position.get('timestamp'))

            delta_gnss = position_timestamp - last_position_timestamp
            timedelta_in_seconds = delta_gnss.total_seconds()

            timedelta_in_hours = abs(timedelta_in_seconds) / 3600.0
            calculated_speed = 0
            distance_moved = 0.0
            if timedelta_in_hours > 0:
                try:  # great_circle is quicker but less accurate than distance function
                    distance_moved = great_circle(
                        (last_position['latitude'],
                         last_position['longitude']),
                        (position['latitude'],
                         position['longitude'])
                    ).km
                except (ValueError, TypeError):
                    logger.debug("Error distance")

                calculated_speed = distance_moved / timedelta_in_hours

            speed = float((position.get('speed') or 0))  # no need to convert

            outlier = any((
                calculated_speed >= MAX_SPEED,
                speed >= MAX_SPEED
            ))

            return outlier

        except (KeyError, TypeError):
            # `last_position` was `None` or malformed.
            pass

    return False


def mark_outlier_positions(positions: list, last_position: dict=None) -> int:
    """
    Mark the outlier positions. if the first position is
    detected as an outlier with respect to next 5 positions then
    remove the first position and repeat recursively until a valid first
    position is found.

    Returns:
         int: outliers_count or 0
    """

    # how many next positions to compare with first position
    default_max_count = 5
    max_first_position_outliers = 5  # to avoid infinite loop

    if not positions:
        return 0

    def find_first_outliers(max_count=5, last_position=None):
        first_few = positions[:-(max_count + 1):-1]
        count = 0
        first_position = positions[-1]
        last_position = last_position or {}
        for position in first_few:
            outlier = is_position_an_outlier(position, last_position)
            if not outlier:
                last_position = position
            else:
                count += 1

        # remove the first(oldest) position if outlier
        if count >= round(max_count / 2):
            positions.remove(first_position)
            return True

        return False

    # detect any first position outlier and remove it
    tries = 1
    last_position = last_position or {}
    while find_first_outliers(default_max_count, last_position) and \
            tries < max_first_position_outliers:
        tries += 1

    # mark positions as outliers
    count = 0
    for position in positions[::-1]:
        outlier = is_position_an_outlier(position, last_position)
        if not outlier:
            last_position = position
        else:
            position['outlier'] = True
            count += 1

    return count
