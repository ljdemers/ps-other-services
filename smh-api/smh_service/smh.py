import time
from datetime import datetime, timedelta
from geopy.distance import great_circle
import copy
from collections import Counter

from api_clients.utils import date2str, str2date, DATE_FORMAT, \
    json_logger, convert_float

from smh_service.clients import ais_client, sis_client, port_service_client
from smh_service.outliers import mark_outlier_positions
from smh_service.ais_track import full_ais_tracks, full_ais_track
from smh_service.models import get_eez

from ps_env_config import config

MIN_DISTANCE_MOVED = 50  # minimum distance moved (in meters) to be considered for speed filtering
MAX_AIS_RATE_TRACK = 240  # the maximum rate at which to store AIS track.
NON_PORT_STOPS_RATE = 60  # The rate at which to detect non-port stops
POSITION_SPLIT_SIZE = 1000
SPEED_FILTER = 99  # default - disabled

logger = json_logger(__name__, level=config.get('LOG_LEVEL'), sort_keys=False)


def is_ais_pos(pos):
    return not ((pos.get('type') and pos.get('type') == 'IHS') or
                pos.get('sail_date_full'))


def get_ship_movement_history_from_ihs(imo_number, stop_date=None, limit=100, max_items=None):
    """
    Query the IHS server for the terrestrial AIS positions which represent
    port visits.

    This function is called by `screen_ship`.

    Args:
        imo_number (str): IMO number of the ship we want to check.
        stop_date (datetime): The selected date offset.
        limit (int): The item limit in the request
        max_items (int): Max. items to process

    Returns:
        list: List of ``ShipMovement`` positions.
    """
    if not imo_number:
        return [], True

    client = sis_client()

    limit_and_offset = limit
    list_kwargs = {
        'imo': imo_number,
        'limit': limit_and_offset,
        'offset': 0,
    }
    if stop_date:
        list_kwargs['timestamp__gte'] = date2str(stop_date,
                                                 date_format=DATE_FORMAT)

    more_responses = True
    movements = []
    while more_responses:
        sis_resp = client.list_ship_movement_history_by_imo(**list_kwargs)

        if sis_resp.error:
            logger.error(
                'Failed to get ship movement data from SIS for ship with IMO '
                '%s : %s',
                imo_number,
                sis_resp.error
            )
            return [], True

        movements.extend(sis_resp['objects'])

        if not sis_resp.meta.get('next') or (max_items and len(movements) > max_items):
            more_responses = False
        else:
            list_kwargs['offset'] += limit_and_offset

    return movements, False


def split_list(alist, wanted_parts=1):
    length = len(alist)
    return [alist[i * length // wanted_parts: (i + 1) * length // wanted_parts]
            for i in range(wanted_parts)]


def get_ports_from_positions(positions, voyage_stopped_speed=None, detect_stops=0):
    """ Get list of port visits for AIS / IHS positions.
    Loop through positions and see if the (lat, lon) is within a port's
    boundary.
    Args:
        positions (list): AIS and IHS positions.
        voyage_stopped_speed: Speed in knots.
        detect_stops (int) 1 to detect non-port stops, 2 to also merge with port calls
    Returns:
        list: List of dicts containing port call information.
    """
    port_visits = []
    last_port = {}
    index = 0
    stopped = 0
    statuses = []
    begin_stop = {}
    non_port_stops = []
    for position in positions:

        index += 1
        speed = position.get('speed') or 0

        # don't include outliers in port calls
        if 'outlier' in position:
            continue

        if not (position['latitude'] and position['longitude']):
            # Sometimes IHS doesn't provide us with a latitude or a
            # longitude.
            continue

        this_port = {}
        if position.get('port', {}).get('port_code', '0') != '0':
            # speed test - no port call if moving
            if voyage_stopped_speed and speed > voyage_stopped_speed:
                continue

            closest_port = position['port']
            this_port = {
                'port': closest_port,
                'ihs_port_name':
                    position.get('port_name', '') + ", " +
                    position.get('country_name', '') + ", " +
                    position.get('ihs_port_geo_id', '') + ", " +
                    str(position.get('hours_in_port', '')),
                'entered': position['timestamp'],
                'departed': position.get('sail_date_full'),
                'speed': position.get('speed'),
                'heading': position.get('heading') or position.get('course'),
                'sail_date_full': position.get('sail_date_full'),
                'type': position.get('status', 'AIS')
                if position.get('sail_date_full') is None else 'IHS',
                'latitude': position['latitude'],
                'longitude': position['longitude']
            }
        else:
            closest_port = None
        # detect stops
        if detect_stops:
            if not this_port and voyage_stopped_speed and speed <= voyage_stopped_speed:
                stopped += 1
                statuses.append(position.get('status'))
                if stopped == 1:
                    begin_stop = position
            else:
                if stopped >= 3:

                    this_stop = {
                        'port': {'port_name': 'stopped', 'port_code': 'STOPPED',
                                 'port_country_name': 'Stop'},
                        'ihs_port_name': stopped,
                        'entered': begin_stop['timestamp'],
                        'departed': position.get('timestamp'),
                        'speed': position.get('speed'),
                        'heading': position.get('heading') or position.get('course'),
                        'type': Counter(statuses).most_common(1)[0][0],
                        'latitude': begin_stop['latitude'],
                        'longitude': begin_stop['longitude']
                    }
                    non_port_stops.append(this_stop)
                    if detect_stops > 1:
                        port_visits.append(this_stop)
                stopped = 0
                statuses = []

        if not closest_port and not last_port:
            continue

        if closest_port and not last_port:

            last_port = this_port
            port_visits.append(last_port)

        elif (
                closest_port and
                last_port and
                last_port['port'] != closest_port
        ):
            # If we haven't picked up ``departed`` from IHS's
            # ``sail_date_full`` then set ``departed`` to
            # ``position.timestamp``
            if last_port['departed'] is None:
                last_port['departed'] = position['timestamp']
            last_port = this_port
            port_visits.append(last_port)

        elif (
                closest_port and
                last_port and
                last_port['port'] == closest_port and
                position.get('sail_date_full') is not None
        ):
            departed = position.get('sail_date_full')
            last_port['departed'] = departed
            last_port['sail_date_full'] = departed

        elif not closest_port and last_port:
            # If we haven't picked up ``departed`` from IHS's
            # ``sail_date_full`` then set ``departed`` to
            # ``position.timestamp``
            if last_port['departed'] is None:
                last_port['departed'] = position['timestamp']

            # Create a new ``last_port`` dictionary.
            last_port = {}

    return port_visits, non_port_stops


def get_ports(positions, table=None, field='eez_', status='1'):
    """
       Detect port (from ports API) or EEZ (from a DB table)

       Args:
           positions (list): List of positions to detect ports/EEZ for
           table (str, optional): EEZ table to use or None to use Ports API
           field (str, optional): EEZ field to use
           status (ste, optional)

       Returns:
           A List - Detected Port/EEZ/region appended to each positions
    """

    positions_with_port = []
    error = None
    if table:  # EEZ/region detection
        resp_ports = list(get_eez(positions, table=table, field_prefix=field, status=status))
    else:  # get ports
        # try 3 times if Port service is busy
        error = False
        resp_ports = []
        et = -1
        for i in range(3):
            error = False
            try:
                resp_ports = list(port_service_client().get_ports(positions))
                break  # if no exception just break
            except:
                error = True
                logger.warning("Port service exception.")
                time.sleep(1)

        if error:
            logger.error("Unable to connect to Port service.")
            resp_ports = [{} for p in positions]

    # logger.debug("Zones", zones=len(resp_ports))

    for a, b in zip(positions, resp_ports):
        d = a.copy()
        d.update({'port': b})
        positions_with_port.append(d)
    return positions_with_port, 'Port Service Exception' if error else None


def _get_position_timestamp(diff, last_pos, current_pos=None):
    return {
        'gap_hours': round(diff / 3600, 3),
        'last_report_timestamp': (last_pos or {}).get('timestamp'),
        'last_report': last_pos,
        'current_report_timestamp': (current_pos or {}).get('timestamp'),
        'current_report': current_pos
    }


def compute_ais_gaps(filtered, last_position, ais_threshold, get_port=1):
    gap_secs = ais_threshold * 3600  # hours to secs
    start = 0
    latest_ts = None
    gaps_list = []
    latest = last_position
    error = None
    st = time.monotonic()
    logger.debug("Detecting AIS reporting gap", gap_secs=gap_secs,
                 length=len(filtered))
    if not latest and filtered:
        latest = filtered[0]  # latest AIS position
        start = 1
    if latest:
        latest_ts = str2date(latest.get('timestamp'))
    if len(filtered) > start:
        diff = 0
        for pos in filtered[start:]:
            if 'outlier' in pos:
                continue

            ts = str2date(pos.get('timestamp'))
            diff = int((ts - latest_ts).total_seconds())
            # remove gaps due to older positions (already in cache)
            if diff < 0:
                continue
            if diff > gap_secs:
                gaps_list.append(_get_position_timestamp(
                    diff, latest, pos))
            latest_ts = ts
            latest = pos

        diff = int((datetime.utcnow() - latest_ts).total_seconds())
        logger.debug('In gap?', ts=latest_ts, now=datetime.utcnow(), diff=diff)
        if diff > gap_secs:
            gaps_list.append(_get_position_timestamp(diff, latest))

    gaps_list.reverse()
    # get port calls for gap locations
    if gaps_list and get_port == 1:
        gap_positions_current = []
        gap_positions_last = []
        for gap in gaps_list:
            current = gap.get('current_report') or {}
            last = gap.get('last_report') or {}
            gap_positions_current.append(current)
            gap_positions_last.append(last)

        logger.debug("Getting ports for gap locations",
                     gap_starts=len(gap_positions_last),
                     gap_ends=len(gap_positions_current))
        port_list_current, error = get_ports(gap_positions_current)
        port_list_last, error = get_ports(gap_positions_last)

        for gap, port_current, port_last in \
                zip(gaps_list, port_list_current, port_list_last):
            if port_current.get('port', {}).get('port_code', '0') != '0':
                gap['current_report'] = port_current
            if port_last.get('port', {}).get('port_code', '0') != '0':
                gap['last_report'] = port_last

    elapsed = round(time.monotonic() - st, 3)
    logger.info("AIS reporting gap Done",
                gaps=len(gaps_list), elapsed=elapsed)
    return gaps_list, elapsed, error


def get_port_visit_data(imo, mmsi=None, get_port=1, limit=100,
                        end_date=None, options=None, rates=None,
                        last_position=None, last_ihs_visit=None,
                        cached_positions=None):
    """
       Main SMH engine

       Args:
           imo (str): IMO number of the ship we want to check.
           mmsi (str): MMSI of the Ship, can be None
           get_port (int): 1 do port calls, 0 (for testing only)
           end_date (datetime): The selected date offset or None.
           limit (int): The item limit in the SIS request
           options (dict):
           rates (list or None)
           last_position: The last AIS position
           last_ihs_visit: The last IHS port call entry timestamp
           cached_positions: from cache if requested otherwise {}
       Returns:
           A Tuple of Visits, Ship data, IHS, AIS positions etc.
    """
    global logger

    at_time = time.monotonic()
    time_elapsed = {}
    sis_error = None
    error = None
    next_link = None

    remove_outliers = int(options.get('remove_outliers', 1))
    ihs_join = int(options.get('ihs_join', 1))
    ais_days = int(options.get('ais_days', 30))
    speed_filter = int(options.get('speed_filter', SPEED_FILTER))
    auto_config = int(options.get('auto_config', 1))
    eez_rate = int(options.get('eez_rate', 0))
    eez_table = options.get('eez_table', 'eez_200nm')
    eez_field = options.get('eez_field', 'eez_')
    eez_join = options.get('eez_join', 0)
    eez_status = options.get('eez_status')
    detect_stops = options.get('detect_stops', 0)
    user = options.get('user')
    downsample_frequency_seconds = None  # disabled by default

    # check if user has down sampling enabled
    is_downsample = config.get('DOWNSAMPLE_USER_LIST')
    if is_downsample and (is_downsample == "All" or user in is_downsample.split(",")):
        downsample_frequency_seconds = int(config.get('DEFAULT_DOWNSAMPLE_FREQUENCY_SECONDS'))
        # if available then check request parameter otherwise use the default setting
        if downsample_frequency_seconds:
            downsample_frequency_seconds = int(options.get('downsample_frequency_seconds',
                                                           downsample_frequency_seconds))

    options["downsample_frequency_seconds"] = downsample_frequency_seconds
    logger.info(f"Downsampling: {downsample_frequency_seconds}, user: {user}")

    ais_gap_rate = int(options.get('ais_gap_rate', 0))
    ais_gap_hours = int(options.get('ais_gap_hours', 6))
    ais_last_midnight = int(options.get('ais_last_midnight', 0))
    use_cached_positions = options.get('use_cached_positions', False)
    simple_smh = options.get('simple_smh', False)

    speed_filters = {}
    ihs_joins = {}
    if not rates:
        rates = [10, 60, 120, 240, 1440, 3600]
    for rate in rates:
        speed_filters[str(rate)] = speed_filter
        ihs_joins[str(rate)] = ihs_join

    if auto_config & 0x01:  # enable speed filtering
        speed_filters['120'] = 1
        speed_filters['60'] = 1
        speed_filters['10'] = 1
    if auto_config & 0x02:  # no IHS join
        ihs_joins['60'] = 0
        ihs_joins['10'] = 0

    options['rates'] = rates
    options['speed_filters'] = speed_filters
    options['ihs_joins'] = ihs_joins

    dt = datetime.utcnow()
    start_date = dt
    if ais_last_midnight == 1:
        start_date = str2date(date2str(dt, DATE_FORMAT))
    stop_date = dt - timedelta(days=ais_days)

    if not end_date:
        end_date = date2str(stop_date)

    stop_date = str2date(end_date)
    stop_date_ihs = stop_date
    if use_cached_positions or not last_ihs_visit:
        # get fresh IHS data
        stop_date_ihs = datetime.utcnow() - timedelta(days=ais_days)
    elif last_ihs_visit:
        stop_date_ihs = str2date(last_ihs_visit)
        # stop_date = stop_date_ihs

    logger = logger.bind(imo_number=imo)
    logger.info("new SMH Dates",
                start_date=start_date,
                stop_date=stop_date,
                stop_date_ihs=stop_date_ihs,
                ais_days=ais_days)

    options["ais_days"] = ais_days
    ship = {}

    st = time.monotonic()
    if mmsi and mmsi != 'null':
        ship = ais_client().get_status(mmsi=str(mmsi))
        if imo is None:
            imo = str(ship.get('imo_number'))
    elif imo:
        ship = sis_client().get_ship_by_imo(imo)
        mmsi = ship.get('mmsi')

    et = time.monotonic() - st
    logger.debug("Found IMO/mmsi..imo=%s, mmsi=%s" % (imo, mmsi),
                 elapsed=et)
    ais_positions = []
    time_elapsed['resolve_ship'] = round(et, 3)

    if mmsi is None or len(mmsi) < 7:
        error = "No or Invalid MMSI"
        static_and_voyage = {}
    else:
        # get static  and voyage
        static_and_voyage = ais_client().get_static_and_voyage(mmsi)

    # get AIS track
    logger.debug("Getting AIS Data", mmsi=mmsi, options=options)
    st = time.monotonic()
    if stop_date and imo:
        ais_positions = list(full_ais_tracks(
            imo, 0, stop_date, count=limit,
            downsample_frequency_seconds=downsample_frequency_seconds)
        )
        if len(ais_positions) == 0:
            logger.warning("No AIS positions found! Try to use MMSI from Ship data or "
                           "get the MMSI from AIS service using get_mmsi_from_imo()")
            mmsi = ais_client().get_mmsi_from_imo(imo=imo)
            logger.info(f"Getting AIS positions using MMSI={mmsi}")
            ais_positions = list(full_ais_track(
                mmsi, imo, stop_date=stop_date, rate=0, count=limit,
                downsample_frequency_seconds=downsample_frequency_seconds)
            )
            if len(ais_positions) > 0:
                options['mmsi_for_track'] = mmsi

    ais_positions = sorted(ais_positions, reverse=True,
                           key=lambda pos: pos['timestamp'])

    et = time.monotonic() - st
    logger.debug("Get AIS data done successfully", elapsed=str(et),
                 data_length=len(ais_positions))
    time_elapsed['get_ais_track'] = round(et, 3)

    # Remove older positions and Mark outliers
    st = time.monotonic()
    outliers_count = None

    def remove_clean(positions):
        # status = None
        # last_status_ts = ts_status = dt
        for pos in positions:
            # invalid position
            if pos.get('latitude') >= 90 or \
                    pos.get('latitude') <= -90 or \
                    pos.get('longitude') >= 180 or \
                    pos.get('longitude') <= -180:
                logger.debug("Invalid Position", pos=pos)
                # ais_positions.remove(pos)
                continue
            ts = str2date(pos.get('timestamp'))
            if ts < stop_date:
                break

            yield pos

    if len(ais_positions) > 1:

        ais_positions = list(remove_clean(ais_positions))

        logger.debug("Remove done successfully",
                     data_length=len(ais_positions))
        time_elapsed['remove_positions'] = round(time.monotonic() - st, 3)

        # Detect outliers
        st = time.monotonic()
        if remove_outliers > 0:
            outliers_count = mark_outlier_positions(ais_positions,
                                                    last_position)

        et = time.monotonic() - st
        logger.debug("Outlier Detection is done successfully", elapsed=et,
                     data_length=len(ais_positions), outliers=outliers_count)

        time_elapsed['outlier_detection'] = round(et, 3)

    options['outliers_count'] = outliers_count
    options['ais_positions_count'] = len(ais_positions)
    # Read IHS movement data
    st = time.monotonic()
    resp_ihs = []
    mmsi_history = []
    if imo:
        mmsi_history = sis_client().list_mmsi_history(imo)
        movements, sis_error = \
            get_ship_movement_history_from_ihs(imo, stop_date_ihs, limit=limit)

        # Filtering IHS movement data
        resp_ihs = []
        for pos in movements:
            pos['timestamp'] = date2str(str2date(pos.get('timestamp')))
            if str2date(pos['timestamp']) > stop_date_ihs:
                pos.update({'type': 'IHS'})
                pos['latitude'] = convert_float(pos.get('latitude'))
                pos['longitude'] = convert_float(pos.get('longitude'))
                pos['sail_date_full'] = date2str(str2date(
                    pos.get('sail_date_full')))
                pos.pop("resource_uri", None)
                pos.pop("ihs_creation_date", None)
                #  pos.pop("ihs_port_geo_id", None)  # Now include it
                pos.pop("ship_name", None)
                pos.pop("ship_type", None)
                pos.pop("extra_data", None)
                pos.pop("imo_id", None)
                resp_ihs.append(pos)

        resp_ihs.reverse()
        et = time.monotonic() - st
        logger.debug("Get IHS data done successfully", elapsed=et,
                     data_length=len(resp_ihs), mmsi_count=len(mmsi_history),
                     stop_date_ihs=stop_date_ihs)
        time_elapsed['get_ihs_movement_data'] = round(et, 3)

    visits = {}
    lengths = {}
    positions = {}
    eez_visits = []
    gaps_list = []
    non_port_stops = []
    options['ais_gaps_count'] = len(gaps_list)
    options['ais_gaps_elapsed'] = 0
    elapsed = time.monotonic() - at_time
    logger.info("SMH Data collection/wrangling done", Elapsed=elapsed,
                ais_data_length=len(ais_positions))
    time_elapsed['data_collection'] = round(elapsed, 3)

    if (len(ais_positions) > 1) or resp_ihs or use_cached_positions:
        # initialize the port service to wake it up (cold restart)
        try:
            port_service_client().check_port()
        except:
            pass

        # perform AIS reporting gap for all good AIS positions
        if not simple_smh and ais_gap_rate == 1:
            filtered = copy.deepcopy(ais_positions)
            filtered.reverse()
            gaps_list, elapsed, error = compute_ais_gaps(filtered,
                                                         last_position,
                                                         ais_gap_hours,
                                                         get_port=0)
            options['ais_gaps_count'] = len(gaps_list)
            options['ais_gaps_elapsed'] = elapsed
            time_elapsed['ais_gaps'] = elapsed

        new_ais_positions = copy.deepcopy(ais_positions)

        # for all rates
        for rate in rates:
            rate_key = str(rate)
            speed_filter = speed_filters[rate_key]
            ihs_join = ihs_joins[rate_key]
            logger.debug("Processing", Rate=rate,
                         speed_filter=speed_filter,
                         ihs_join=ihs_join, ais=len(ais_positions))
            filtered = []

            # get from cache to do cache rebuilt
            if use_cached_positions and cached_positions:
                ais_positions = copy.deepcopy(new_ais_positions)
                # get only AIS positions and in reverse order
                cached_rate_key = str(rate if rate > MAX_AIS_RATE_TRACK else MAX_AIS_RATE_TRACK)
                old_positions = [pos for pos in cached_positions.get(cached_rate_key, [])[::-1]
                                 if is_ais_pos(pos)]
                ais_positions.extend(old_positions)

                stop_date = str2date(ais_positions[-1].get('timestamp'))
                logger.info("Using cached positions",
                            cached=len(cached_positions.get(cached_rate_key, [])),
                            old_positions=len(old_positions),
                            new_ais_positions=len(new_ais_positions),
                            stop_date=stop_date,
                            total=len(ais_positions))

            latest_ts = datetime.now()
            if ais_positions:
                latest = ais_positions[0]  # latest AIS position
                latest_ts = str2date(latest.get('timestamp'))
                logger.debug(latest_position=latest)
            st1 = time.monotonic()

            # Perform rate reduction
            for pos in ais_positions:
                ts = str2date(pos.get('timestamp'))

                diff = (latest_ts - ts).total_seconds()
                if (diff == 0 or diff >= (60 * rate)) and \
                        start_date >= ts >= stop_date:
                    filtered.append(pos)
                    latest_ts = ts

            # Always keep the last position
            last = None
            if filtered:
                last = filtered[-1]
                logger.debug(last_position=last)
                if last.get('timestamp') != ais_positions[-1].get('timestamp'):
                    filtered.append(ais_positions[-1])

            logger.debug("filtered positions", data_length=len(filtered))

            filtered.reverse()
            lengths[rate_key] = len(filtered)

            # perform AIS reporting gap at this rate (optional feature)
            if not simple_smh and ais_gap_rate == rate:
                gaps_list, elapsed, error = compute_ais_gaps(filtered,
                                                             last_position,
                                                             ais_gap_hours)
                options['ais_gaps_count'] = len(gaps_list)
                options['ais_gaps_elapsed'] = elapsed
                time_elapsed['ais_gaps'] = elapsed

            # speed filtering
            # no filtering if disable >= SPEED_FILTER
            if (speed_filter < SPEED_FILTER) and filtered:
                last = filtered[0]
                speed_filtered = [last]
                last_speed = last.get('speed')
                stopped = 5 if not last_speed or last_speed < speed_filter else 0
                count = 0
                for pos in filtered[1:-1]:
                    distance_moved = great_circle(
                        (last['latitude'],
                         last['longitude']),
                        (pos['latitude'],
                         pos['longitude'])
                    ).m
                    count += 1
                    last = pos

                    if distance_moved < MIN_DISTANCE_MOVED:
                        continue
                    pos_speed = pos.get('speed')
                    if not pos_speed or pos_speed < speed_filter:
                        stopped = 5
                        speed_filtered.append(pos)
                    elif stopped:
                        speed_filtered.append(pos)
                        stopped -= 1

                speed_filtered.append(filtered[-1])

                et = time.monotonic() - st1
                logger.debug("Speed filtering done successfully", elapsed=et,
                             data_length=len(speed_filtered))
            else:
                speed_filtered = filtered

            resp_positions = copy.deepcopy(speed_filtered)
            # add IHS if flag set
            if ihs_join == 1:
                resp_positions.extend(resp_ihs)
                logger.debug("IHS_joined", IHS_joined_positions=len(resp_positions))

            # sort by timestamp, keeping valid positions
            resp_positions = [p for p in sorted(resp_positions,
                                                key=lambda pos: pos[
                                                    'timestamp'])
                              if p['latitude']]

            st = time.monotonic()
            if get_port == 1:
                resp_dict = []
                parts = len(resp_positions)//POSITION_SPLIT_SIZE + 1
                logger.debug("Position List split", positions=len(resp_positions), parts=parts)

                for ports in split_list(resp_positions, parts):
                    response_ports, error = get_ports(ports)  # error is returned by the function
                    resp_dict.extend(response_ports)
                visits[rate_key], stops = get_ports_from_positions(
                    resp_dict,
                    speed_filter,
                    detect_stops if rate == NON_PORT_STOPS_RATE else 0
                )
                if rate == NON_PORT_STOPS_RATE:
                    non_port_stops = copy.deepcopy(stops)
                    options['non_port_stops_rate'] = NON_PORT_STOPS_RATE
                    logger.info("saving non_port_stops..", non_port_stops=len(non_port_stops))

                logger.debug("visits", visits=len(visits[rate_key]))
                visits[rate_key].reverse()
                time_elapsed['get_ports_'+rate_key] = round(time.monotonic() - st, 3)

            #  EEZ (Exclusive Economic Zone) or any region detection for the specific rate
            # if enabled (set to one of the AIS rates). It uses either
            # 12 nautical miles zone or 200 miles zones (polygons) or
            # any defined list of regions in 'eez_table'. This table should already
            # be populated in SMH DB in the desired env.
            if not simple_smh and eez_rate == rate:  # only for one rate
                resp_dict = []
                try:
                    resp_dict, error = get_ports(resp_positions, table=eez_table,
                                                 field=eez_field, status=eez_status)
                    eez_visits.extend(get_ports_from_positions(resp_dict)[0])
                    eez_visits.reverse()
                    if eez_join:
                        visits[rate_key].extend(eez_visits)
                        visits[rate_key].reverse()
                        visits[rate_key] = sorted(visits[rate_key], reverse=True,
                                                  key=lambda pos: pos['entered'])
                    et = time.monotonic() - st
                    logger.info("EEZ/Region Done", Rate=rate, elapsed=str(et))
                    options['eez_elapsed'] = et
                    time_elapsed['eez_elapsed'] = round(et, 3)
                except Exception as exc:
                    logger.warning("EEZ lookup Failed!", exception=str(exc))

            et = time.monotonic() - st
            logger.info("Ports Done", Rate=rate, elapsed=str(et), data=len(speed_filtered))
            if rate >= MAX_AIS_RATE_TRACK:
                positions[rate_key] = speed_filtered  # only AIS positions
            time_elapsed[rate_key] = round(elapsed + (time.monotonic() - st1), 3)
    elif options.get('use_cache', 1) == 0 and not error:
        next_link = "No Position Data Found"
        error = next_link

    return \
        ais_positions, resp_ihs, visits, dict(ship), time_elapsed, \
        next_link, error or ('SIS error' if sis_error else None), positions, \
        options, mmsi_history, gaps_list, eez_visits, \
        dict(static_and_voyage), lengths, non_port_stops
