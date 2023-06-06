import json
from datetime import datetime, timedelta

from api_clients.utils import str2date, json_logger, date2str
from smh_service.clients import ais_client, sis_client

from ps_cassandra_ais20.track_data import get_complete_track_data
from ps_env_config import config

logger = json_logger(__name__, level=config.get('LOG_LEVEL'), sort_keys=False)


def full_ais_tracks(imo_number, rate=60, stop_date=None, count=500,
                    downsample_frequency_seconds=None):
    """ Retrieve the full movement history for a ship (with mmsi history)

    Args:
        imo_number (`obj`: str): 7 digital IMO number to be
            used to retrieve MMSI history.
        rate (int): filtering rate during track read (0 for no filtering yet)
        stop_date (datetime): Datetime to capture the data from
        count (int): No. of positions to extract per request
        downsample_frequency_seconds (None or int):
    Returns:
        generator of positions
    """
    mmsi_history = sis_client().list_mmsi_history(imo_number, order_by="effective_from")
    for index, history in enumerate(mmsi_history['objects']):
        logger.debug("MMSI history", mmsi_history=history, index=index, stop_date=stop_date)

        # Parse the timestamps from SIS response.
        if index == 0:
            from_date = stop_date  # go all the way back in history
        else:
            from_date = str2date(history['effective_from'])
        try:
            to_date = str2date(history['effective_to'])

        except TypeError:
            to_date = None  # still effective
        yield from full_ais_track(
            mmsi=history.get('mmsi'),
            imo_number=imo_number,
            from_date=from_date,
            to_date=to_date,
            stop_date=stop_date,
            rate=rate,
            count=count,
            downsample_frequency_seconds=downsample_frequency_seconds
        )


def full_ais_track(
        mmsi=None, imo_number=None,
        from_date=None, to_date=None,
        stop_date=None,
        rate=60,
        count=500,
        downsample_frequency_seconds=None
):
    """ Retrieve the full movement history for a ship.
    Either IMO or MMSI needs to be passed

    Args:
        mmsi (`obj`:str, optional): The MMSI of the ship being retrieved (9
            digits).
        imo_number (`obj`: str, optional): Optional 7 digital IMO number to be
            used to retrieve AIS's stored MMSI.
        from_date (`obj`: datetime, optional): Optional from_date limit.
            Otherwise stop_date will be used.
        to_date (`obj`: datetime, optional): Optional to_date limit.
            Otherwise current datetime will be used.
        rate (int): filtering rate for AIS track
        stop_date (`obj`: datetime): AIS track stop date doing backward
        count (int): No. of positions to extract per request
        downsample_frequency_seconds (None or int):
    Returns:
        generator of positions
    """
    if not (mmsi or imo_number):
        raise ValueError(
            'Didn\'t receive an MMSI or IMO when attempting to retrieve '
            'full AIS track'
        )

    tdelta = timedelta(minutes=int(rate))

    now = datetime.utcnow()

    # use start date but not smaller than stop date
    # (AIS track stop date doing backward)
    from_date_min = stop_date
    logger.debug("AIS track config", mmsi=mmsi,
                 from_date_min=from_date_min,
                 from_date=from_date)

    from_date = (
        max(from_date, from_date_min) if from_date else from_date_min
    )

    # use end date but not bigger than current datetime
    to_date_max = now
    to_date = min(to_date, to_date_max) if to_date else to_date_max

    current_timestamp = previous_timestamp = to_date
    security_counter = 0

    def filter_positions(previous, current):
        """
        Filters positions based on timestamps.

        Args:
            previous (datetime.datetime): Previous time.
            current (datetime.datetime): Current time.

        Returns:
            bool: ``True`` if previous time is bigger, ``False`` otherwise.
        """
        if previous - tdelta < current:
            return False

        return True

    while current_timestamp > from_date:
        use_ais = config.get('USE_AISAPI') == 'True'
        if use_ais:
            track = ais_client().get_track(
                mmsi=mmsi,
                limit=count,
                end_date=current_timestamp,
                downsample_frequency_seconds=downsample_frequency_seconds
            ).get("data", [])
        else:
            req_dates = {
                "end_date": current_timestamp,
            }
            limit = count
            track = get_complete_track_data(mmsi=int(mmsi),
                                            request_dates=req_dates,
                                            position_count=limit,
                                            downsample_frequency_seconds=downsample_frequency_seconds)

        logger.debug("Data extracted", mmsi=mmsi, count=len(track),
                     current=current_timestamp)

        if not track:
            msg = f"track returned no results for mmsi={mmsi} and end_date={current_timestamp}"
            logger.info(msg)
            return

        for position in track:
            if not use_ais:
                raw_ts = position.get("timestamp")
                row_dt_string = date2str(datetime.utcfromtimestamp(raw_ts))
                position["timestamp"] = row_dt_string
                position["extdata"] = json.loads(position["extdata"])
            position.pop('extdata', None)
            position.pop('channel', None)
            security_counter += 1
            if security_counter > \
                    int(config.get('AIS_MAX_POSITIONS_FOR_SCREENING')):
                logger.debug("Too many positions", security_counter=security_counter,
                             current_timestamp=current_timestamp)
                return

            position_timestamp = str2date(position['timestamp'])
            current_timestamp = position_timestamp

            # start date filter for AIS positions
            if current_timestamp < from_date:
                return

            if rate > 0 and not filter_positions(previous_timestamp,
                                                 current_timestamp):
                continue

            previous_timestamp = current_timestamp
            yield position
