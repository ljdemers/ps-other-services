import orjson as json
import time
from datetime import datetime, timedelta
from enum import Enum
from flask import Response

from api_clients.utils import json_logger, date2str, str2date, convert_float
from api_clients.utils import json_zip

from smh_service.smh_api_schema import SMHDataDictSchema, SMHDataDictMiscDataSubschema
from smh_service.smh import get_port_visit_data, \
    get_ship_movement_history_from_ihs, is_ais_pos, MAX_AIS_RATE_TRACK
from smh_service.clients import statsd_client
from smh_service.models import SMHData

from ps_env_config import config

logger = json_logger(__name__, level=config.get('LOG_LEVEL'), sort_keys=False)
stats = statsd_client()


# possible values for check_for_ihs_updates:
# 0 = don't check for IHS updates
# 1 = check of IHS updates (entry timestamp only) and do cache rebuild, default
# 2 = check of IHS updates (any item in the record) and do cache rebuild
# 3 = check of IHS updates (entry timestamp only) but just mark it without any cache rebuild
# 4 = check of IHS updates (entry timestamp only) but just update IHS data in cache
class IhsUpdateChecks(Enum):
    DISABLED = 0
    REBUILD_ON_TIMESTAMP = 1
    REBUILD_ON_ITEM = 2
    CHECK_BUT_NO_REBUILD = 3
    JUST_REBUILD_IHS = 4


class SMHTask:
    options = None

    def __init__(self, imo_number, options):
        """
        Initialize the SMH Task object with IMO and requested options.
        Args:
            imo_number (str): IMO number of the ship we want to check (required).
            options (dict):
        """
        self.start_time = 0
        self.end_date = None
        self.imo_number = imo_number
        self.options = options
        self.visit_list_dict = {}
        self.position_list_dict = {}
        self.ihs_list = []
        self.gaps_list = []
        self.eez_visit_list = []
        self.ship_data = {}
        self.mmsi_history = []
        self.static_and_voyage = {}
        self.elapsed = {}
        self.lengths = {}
        self.ais_track = []
        self.cached_datetime = None
        self.last_position = None
        self.last_ihs_visit = None
        self.new_visits = {}
        self.new_positions = {}
        self.ihs_list_updated = None
        self.non_port_stops = []

    @stats.timer('prepare_response_elapsed')
    def prepare_response(self):
        """
        Prepare the response and SMH data objects.
        Returns:
            The JSON response object.
        """
        self.options['imo_number'] = self.imo_number
        self.options['elapsed_seconds'] = self.elapsed.get('total_time')
        self.elapsed['read_cache_elapsed'] = self.options.get('read_cache_elapsed')
        max_items = self.options.get('max_items_per_object')
        detect_stops = self.options.get('detect_stops', 0)

        metadata = self.options
        metadata['elapsed'] = self.elapsed
        rate = int(self.options.get('ais_rate'))
        visits = self.visit_list_dict.get(str(rate), [])
        positions = self.position_list_dict.get(
            str(rate if rate > MAX_AIS_RATE_TRACK else MAX_AIS_RATE_TRACK), []
        )
        ihs_data = self.ihs_list
        gap_data = self.gaps_list

        metadata['positions'] = len(positions)
        metadata['ihs_movement_data'] = len(ihs_data)
        if gap_data:
            metadata['ais_gaps_count'] = len(gap_data)
        if self.eez_visit_list:
            metadata['eez_visits'] = len(self.eez_visit_list)

        # remove non-port stops if any
        stops = []
        if detect_stops > 2:
            logger.info("Removing non-port stops", items=len(visits))
            for visit in visits:
                port_code = visit['port']['port_code']
                if port_code == "STOPPED":
                    stops.append(visit)
            visits = [item for item in visits if item not in stops]
            # visits = list(set(visits) - set(stops))
            logger.info("non-port stops removed", visits=len(visits), stops=len(stops))

        metadata['visits'] = len(visits)
        port_filter = self.options.get('port_filter')
        port_count_limit = self.options.get('port_count_limit')
        if port_filter and len(port_filter) > 1 and len(visits) > 0:
            # metadata['port_filter'] = port_filter
            logger.info(f"Applying Port filter ({port_filter})",
                        visits=metadata['visits'])
            filtered_visits = []
            for visit in visits:
                port_code = visit['port']['port_code']
                for port_abbr in port_filter.split(','):
                    if port_code.startswith(port_abbr):
                        filtered_visits.append(visit)

            metadata['filtered_visits'] = len(filtered_visits)
            visits = filtered_visits
            logger.debug(f"Port filter Applied ({port_filter})",
                         visits=len(visits))

        ais_days = self.options.get('ais_days')
        request_days = int(self.options.get('request_days'))
        count_visits = len(visits)
        count_positions = len(positions)
        count_ihs = len(ihs_data)

        if ais_days and request_days and request_days < ais_days:
            start_date = datetime.utcnow() - timedelta(days=request_days)
            logger.debug(f"Applying interval filter ({request_days} < "
                         f"{ais_days})", visits=metadata['visits'],
                         positions=metadata['positions'],
                         start_date=start_date)

            if count_positions and \
                    str2date(positions[-1].get('timestamp') or '1970-01-01') < start_date:
                positions = []  # no positions since the requested start date

            for pos in positions[::-1]:
                if str2date(pos.get('timestamp')) >= start_date:
                    count_positions -= 1
                else:
                    break

            count_ihs = 0
            for pos in self.ihs_list:
                if str2date(pos.get('timestamp')) >= start_date:
                    count_ihs += 1
                else:
                    break

            count_visits = 0
            for pos in visits:
                if (str2date(pos.get('departed') or
                             pos.get('entered'))) >= start_date:
                    count_visits += 1
                else:
                    break

            count = 0
            for pos in gap_data:
                if (str2date(pos.get('current_report_timestamp') or
                             pos.get('last_report_timestamp'))) >= start_date:
                    count += 1
                else:
                    break
            gap_data = gap_data[:count]

        # check if port_count_limit is in valid range
        if 0 < port_count_limit < len(visits):
            visits = visits[:port_count_limit]
            metadata['filtered_visits'] = len(visits)

        # max item filtering if enabled (return latest data)
        visits = visits[:max_items] if max_items and count_visits > max_items else \
            visits[:count_visits]
        ihs_data = ihs_data[:max_items] if max_items and count_ihs > max_items else \
            ihs_data[:count_ihs]

        every = None
        if count_positions < metadata['positions']:
            positions = positions[count_positions:]
        # skipping positions if needed to return under max_items position
        if max_items and len(positions) > max_items:
            every = (len(positions) * 2) //max_items
            positions = positions[::every]

        metadata['response_visits'] = len(visits)
        metadata['response_non_port_stops'] = len(stops)
        metadata['response_ihs_data'] = len(ihs_data)
        metadata['response_positions'] = len(positions)
        metadata['position_skip'] = every

        metadata['flag_name'] = self.ship_data.get('flag_name')
        metadata['ship_name'] = self.ship_data.get('ship_name')
        metadata['mmsi'] = self.ship_data.get('mmsi') or self.options.get('mmsi_for_track')
        metadata['shiptype_level_5'] = self.ship_data.get('shiptype_level_5')
        metadata['ship_status'] = self.ship_data.get('ship_status')
        metadata['draught'] = self.static_and_voyage.get('draught')
        metadata['destination'] = self.static_and_voyage.get('destination')

        response_json = {'metadata': metadata}

        # Response with objects as requested..
        # for example: response_type = 0x07 will response with 3 objects:
        #       1. Port visits
        #       2. Positions used for port detection
        #       3. IHS movement data
        # This setting (0x07) is required for Ptrac
        response_type = int(self.options.get('response_type') or 0x07)

        if response_type & 0x01:  # just response with port visits
            response_json['visits'] = visits
        if response_type & 0x02:
            response_json['positions'] = positions
        if response_type & 0x04:
            response_json['ihs_movement_data'] = ihs_data
        if response_type & 0x08:  # full AIS track
            response_json['track'] = self.ais_track
        if response_type & 0x10:
            response_json['ship_status'] = self.ship_data
        if response_type & 0x20:
            response_json['ais_gaps'] = gap_data
        if response_type & 0x40:
            response_json['eez_visits'] = self.eez_visit_list
        if response_type & 0x80:
            response_json['static_and_voyage'] = self.static_and_voyage
            response_json['non_port_stops'] = stops

        logger.debug("Response Ready", response_type=response_type,
                     visits=len(visits), positions=len(positions),
                     ihs=len(ihs_data), gaps=len(gap_data))

        return Response(json.dumps(response_json), mimetype='application/json')

    #  Write SMH results in DB
    @stats.timer('cache_results_elapsed')
    def cache_results(self, app):
        start = time.monotonic()
        cache_table = None
        try:

            last_id = self.options.get('last_smh_id')
            overwrite_cache = self.options.get('overwrite_cache')
            save_port_visits = self.options.get('save_port_visits', 0)  # depreciated
            use_new_cache_table = self.options.get('use_new_cache_table', True)  # depreciated
            zip_data = self.options.get('zip_data')

            smh_data_schema = SMHDataDictSchema()
            cache_table = "smh_data"

            screen_datetime = self.options.get('screened_date')
            smh_timestamp = str2date(screen_datetime) if screen_datetime else datetime.utcnow()

            # optionally ZIP ihs, gaps and position data for faster cache read/write
            # This option is settable by 'zip_data' query parameter (disabled by default)
            smh_data_dict = smh_data_schema.dump(dict(
                timestamp=smh_timestamp,
                imo_number=self.imo_number,
                cached_days=self.options.get('ais_days'),
                options=self.options,
                port_visits=self.visit_list_dict,
                positions=json_zip(self.position_list_dict)
                if zip_data else self.position_list_dict,
                ais_gaps=[json_zip(self.gaps_list)] if zip_data else self.gaps_list,
                eez_visits=self.eez_visit_list,
                ihs_movements=[json_zip(self.ihs_list)] if zip_data else self.ihs_list,
                misc_data=SMHDataDictMiscDataSubschema().dump(dict(
                    mmsi_history=self.mmsi_history,
                    ship_status=self.ship_data,
                    static_and_voyage=self.static_and_voyage,
                    elapsed=self.elapsed,
                    lengths=self.lengths,
                    non_port_stops=self.non_port_stops
                )),
            ))
            with app.app_context():
                SMHData().insert_update_smh_data(smh_data_dict, last_id, overwrite_cache)

            logger.info("SMH data Saved",
                        elapsed=time.monotonic() - start,
                        id=last_id, zip_data=zip_data,
                        data_size=len(str(smh_data_dict)),
                        positions=len(self.position_list_dict.get('3600', [])),
                        gaps=len(self.gaps_list),
                        ihs=len(self.ihs_list)
            )

        except Exception as exp:
            logger.error("DB write Error", Exception=str(exp))

        return cache_table

    @stats.timer('read_cache_elapsed')
    def get_cached_smh(self, end_date):
        """
           Extract cached SMH object if available

           Args:
               end_date (datetime): The selected date offset or None.
           Returns:
               A Tuple of Visits, Ship data, IHS, AIS positions etc.
        """
        self.start_time = time.monotonic()
        self.end_date = end_date
        use_cache = self.options.get('use_cache', 1)
        ais_gap_rate = self.options.get('ais_gap_rate', 1)
        ais_days = self.options.get('ais_days')
        eez_rate = self.options.get('eez_rate')
        max_items = self.options.get('max_items_per_object')
        use_cached_positions = self.options.get('use_cached_positions', False)

        last_smh = {}
        last_id = None
        cached_positions = {}
        stats.incr('smh_requested')  # count of SMH requested
        if self.options.get('user'):
            stats.incr('smh_requested_' + self.options.get('user'))

        update = use_cache - 1
        if update >= 0 and self.imo_number:
            logger.info("Getting Cached SMH results",
                        imo_number=str(self.imo_number))

            try:
                # retrieve the latest SMH results
                options, self.visit_list_dict, self.position_list_dict, \
                    ihs_list, gaps_list, eez_visit_list = \
                    SMHData().get_cached_smh_data(self.imo_number, update)

                last_smh['options'] = options
                last_smh['ihs'] = ihs_list
                last_smh['ais_gaps'] = gaps_list
                self.options['read_cache_elapsed'] = round(time.monotonic() - self.start_time, 3)
                if options:
                    try:
                        last_options = last_smh.get('options', {})
                        last_id = last_options.get('id')
                        self.options['last_update_count'] = last_options.get('update_count', 0)
                        self.options['read_db_elapsed'] = last_options.get('read_db_elapsed')
                        self.cached_datetime = last_options.get('timestamp')
                        if isinstance(self.cached_datetime, str):
                            self.cached_datetime = str2date(self.cached_datetime)
                        if ais_gap_rate > 0:
                            rate = MAX_AIS_RATE_TRACK if ais_gap_rate == 1 else ais_gap_rate
                            positions = self.position_list_dict.get(str(rate), [])
                            if positions:
                                self.last_position = positions[-1]
                                logger.debug("Last_position", pos=self.last_position)

                        if use_cached_positions:
                            cached_positions = self.position_list_dict
                        cached_days = last_options.get('ais_days', 0)

                        stop_date = date2str(self.cached_datetime - timedelta(seconds=5))
                        begin_date = self.cached_datetime - timedelta(days=cached_days)

                        if self.end_date and str2date(self.end_date) < begin_date:
                            raise Exception("Not enough cached data")

                        current_timestamp = datetime.utcnow()

                        begin_days = (current_timestamp - begin_date).days
                        if ais_days and begin_days < ais_days:
                            raise Exception("Not enough cached data.")

                        # check for IHS back-filled data,
                        # optionally only for IMO with IHS data size < max_items
                        if self.options.get('check_for_ihs_updates') and ihs_list:
                            # ignore it too many IHS data to process
                            if max_items and len(ihs_list) > max_items:
                                self.options['ihs_updated'] = False
                            else:
                                ihs_updated = self.check_for_ihs_update(ais_days, ihs_list)
                                self.options['ihs_updated'] = ihs_updated

                                # if check_for_ihs_updates is set to 3 or no need to join
                                # then just mark it that it is missing data but no cache rebuild
                                check_for_ihs_updates = \
                                    IhsUpdateChecks(self.options['check_for_ihs_updates'])
                                if ihs_updated and check_for_ihs_updates not in \
                                        [IhsUpdateChecks.CHECK_BUT_NO_REBUILD,
                                         IhsUpdateChecks.JUST_REBUILD_IHS] and \
                                        self.options['ihs_join'] != 0:
                                    # count of cache rebuild due to IHS back-filled data
                                    stats.incr('cache_rebuild_IHS')
                                    raise Exception(f"Cached invalidated - Some IHS data "
                                                    f"has been updated! "
                                                    f"(for IMO: {self.imo_number} "
                                                    f"at {ihs_updated})")

                        # new cache if eez rate is different or was not in cache
                        last_eez_rate = last_options.get('eez_rate')
                        if eez_rate and (not last_eez_rate or last_eez_rate != eez_rate):
                            raise Exception(f"New Cache needed - New EEZ rate {eez_rate}")

                        self.end_date = stop_date
                        if ihs_list:
                            self.last_ihs_visit = ihs_list[0].get('timestamp')
                        self.options['read_process_elapsed'] = round(
                            time.monotonic() - self.start_time, 3)
                        logger.info("Cached SMH",
                                    elspaed=self.options['read_process_elapsed'],
                                    last_SMH_id=str(last_id),
                                    last_SMH_date=date2str(self.cached_datetime),
                                    last_ihs=self.last_ihs_visit,
                                    cached_days=cached_days,
                                    end_date=self.end_date)

                    except Exception as exc:
                        # in case of exception, cached results are unusable
                        # and therefore perform a clean SMH
                        last_smh = None
                        last_id = None
                        self.last_position = None
                        logger.warning("Performing a new SMH",
                                       imo_number=self.imo_number,
                                       exception=str(exc))
            except Exception as exc:
                logger.error("DB error", exception=str(exc))
                raise

        self.options['last_smh_id'] = last_id
        return last_smh, cached_positions

    @stats.timer('perform_smh_elapsed')
    def get_smh_results(self, last_smh, cached_positions):
        # perform the SMH
        smh_datetime = datetime.utcnow()
        limit = self.options.get('limit', 100)

        try:
            if not last_smh:
                self.end_date = None
            logger.info("Perform SMH", end_date=self.end_date)
            self.ais_track, self.ihs_list, visits, self.ship_data, self.elapsed, _, \
                error, resp_positions, self.options, mmsi_history, \
                self.gaps_list, self.eez_visit_list, \
                self.static_and_voyage, self.lengths, self.non_port_stops = \
                get_port_visit_data(
                    self.imo_number, limit=limit, get_port=1,
                    end_date=self.end_date,
                    options=self.options,
                    last_position=self.last_position,
                    last_ihs_visit=self.last_ihs_visit,
                    cached_positions=cached_positions
                )

            self.mmsi_history = dict(mmsi_history).get('objects', [])
            self.options['cache_updated'] = 0
            if resp_positions or visits or self.ihs_list or self.ihs_list_updated:
                self.options['cache_updated'] = 1
                stats.incr('cache_updated')  # count of SMH cache updated
            self.new_visits = visits
            self.new_positions = resp_positions
        except Exception as exc:
            error = str(exc)
            self.options['error'] = error
            logger.error("Exception", Exception_in_SMHTask=error, imo_number=self.imo_number)
            raise

        self.options['mmsi_count'] = len(mmsi_history.get('objects', []))
        self.options['error'] = error

        self.elapsed['total_time'] = round(time.monotonic() - self.start_time, 3)
        logger.info("SMH done", elapsed=self.elapsed.get('total_time'))
        if smh_datetime:
            self.options['screened_date'] = date2str(smh_datetime)

    @stats.timer('update_cache_elapsed')
    def update_cache(self, last_smh):

        if self.cached_datetime and last_smh:
            use_cached_positions = self.options.get('use_cached_positions', False)
            last_options = last_smh.get('options', {})
            last_ports_days = int(last_options.get('ais_days', 0))
            smh_count = int(last_options.get('smh_count', 1))
            ports_days = int(self.options.get('ais_days') or 0)
            current_timestamp = datetime.utcnow()
            # current_timestamp = datetime.now(timezone.utc) \
            #    if self.options.get('old_cache', 1) else datetime.utcnow()
            ais_days_since_last = (current_timestamp - self.cached_datetime).days

            self.options['ais_days_last'] = last_ports_days
            self.options['ais_days_current'] = ports_days
            self.options['ais_days_since_last'] = ais_days_since_last
            self.options['ais_days'] = last_ports_days + ais_days_since_last
            self.options['smh_count'] = smh_count + 1
            self.options['outliers_count'] = \
                (self.options.get('outliers_count') or 0) + \
                (last_options.get('outliers_count') or 0)
            self.options['ais_positions_count'] = \
                self.options.get('ais_positions_count', 0) + \
                last_options.get('ais_positions_count', 0)
            self.options['ais_gaps_count'] = \
                self.options.get('ais_gaps_count', 0) + \
                last_options.get('ais_gaps_count', 0)
            self.options['ais_gaps_elapsed'] = \
                self.options.get('ais_gaps_elapsed', 0) + \
                last_options.get('ais_gaps_elapsed', 0)

            self.options['first_smh_timestamp'] = \
                last_options.get('first_smh_timestamp') or \
                date2str(self.cached_datetime)

            joined_visits = self.visit_list_dict  # last_smh.get('visits', {})
            joined_positions = self.position_list_dict  # last_smh.get('positions', {})
            last_eez_visits = last_smh.get('eez_visits', [])
            if self.ihs_list_updated:  # need to update IHS data
                last_ihs = self.ihs_list_updated
            else:
                last_ihs = last_smh.get('ihs', [])

            last_ais_gaps = last_smh.get('ais_gaps', [])
            logger.info("SMH old",
                        positions=len(self.position_list_dict.get('3600', [])),
                        visits=len(self.visit_list_dict.get('3600', [])),
                        gaps=len(last_ais_gaps),
                        ihs=len(last_ihs))
            if use_cached_positions:
                joined_visits = self.new_visits
                joined_positions = self.new_positions
            else:
                for k, p in self.new_visits.items():
                    ports = p
                    last_visits = self.visit_list_dict.get(str(k), [])
                    last_visit_departed = None
                    last_visit_entered = None
                    if last_visits and ports:
                        new_visit_entered = ports[-1]["entered"]
                        # remove redundant calls
                        while last_visits:
                            last_visit_entered = last_visits[0].get("entered")
                            last_visit_departed = last_visits[0].get("departed")
                            if new_visit_entered > last_visit_entered:
                                break
                            last_visits.pop(0)

                        if not last_visit_departed and last_visits:
                            last_port = last_visits[0].get("port", {}).get("port_code")
                            new_port = ports[-1].get("port", {}).get("port_code")

                            if new_port == last_port:
                                ports[-1]["entered"] = last_visit_entered
                                last_visits.pop(0)
                            else:
                                last_visits[0]["departed"] = ports[-1]["entered"]

                    logger.debug("Joining", rate=k, last_visits_length=len(last_visits),
                                 new_visits_length=len(ports))
                    ports.extend(last_visits)
                    joined_visits[k] = ports

                for k, p in self.new_positions.items():
                    # positions = p
                    last_all = self.position_list_dict.get(str(k), [])
                    last = [pos for pos in last_all if is_ais_pos(pos)]
                    logger.debug("Last positions", rate=k,
                                 all=len(last_all), len=len(last), new=len(p))
                    if p:
                        new_timestamp = p[0].get("timestamp")
                        # remove redundant positions
                        while last:
                            last_timestamp = last[-1].get("timestamp")
                            if new_timestamp > last_timestamp:
                                break
                            last.pop(-1)

                    logger.debug("Last positions Removed", len=len(last), rate=k)
                    last.extend(p)
                    joined_positions[k] = last

                # join IHS data and EEZ visits
                self.ihs_list.extend(last_ihs)
                self.eez_visit_list.extend(last_eez_visits)

            # remove the last gap if it was on going
            if self.gaps_list and last_ais_gaps and isinstance(last_ais_gaps, list) and \
                    last_ais_gaps[0].get('current_report_timestamp') is None:
                last_ais_gaps.pop(0)
            self.gaps_list.extend(last_ais_gaps)  # join gaps data

            self.elapsed['total_time'] = time.monotonic() - self.start_time
            self.visit_list_dict = joined_visits
            self.position_list_dict = joined_positions

            logger.info("Joined SMH done",
                        elapsed=self.elapsed['total_time'],
                        visits=len(self.visit_list_dict.get('3600', [])),
                        gaps=len(self.gaps_list),
                        positions=len(self.position_list_dict.get('3600', [])))
        else:  # new SMH
            self.options['smh_count'] = 1
            self.options['first_smh_timestamp'] = self.options['screened_date']
            self.visit_list_dict = self.new_visits
            self.position_list_dict = self.new_positions

        return

    @stats.timer('check_ihs_update_elapsed')
    def check_for_ihs_update(self, ais_days, ihs_visits):
        # check if IHS movement data is updated
        # if ihs_join = 0 and check_for_ihs_updates in [1, 2] then also only
        # update IHS data in cache

        stop_date_ihs = datetime.utcnow() - timedelta(days=ais_days)
        ihs_movements, _ = get_ship_movement_history_from_ihs(
            self.imo_number, stop_date_ihs, limit=self.options.get('limit', 100))

        resp_ihs = []
        last_ihs_visit_timestamp = str2date(ihs_visits[0].get('timestamp'))

        for pos in ihs_movements[::-1]:  # reverse
            pos['timestamp'] = date2str(str2date(pos.get('timestamp')))
            if last_ihs_visit_timestamp and str2date(pos['timestamp']) <= last_ihs_visit_timestamp:
                pos.update({'type': 'IHS'})
                pos['latitude'] = convert_float(pos.get('latitude'))
                pos['longitude'] = convert_float(pos.get('longitude'))
                pos['sail_date_full'] = date2str(str2date(pos.get('sail_date_full')))
                resp_ihs.append(pos)

        logger.debug("IHS update", check_for_ihs_updates=self.options['check_for_ihs_updates'],
                     stop_date_ihs=stop_date_ihs,
                     last_ihs_visit_timestamp=last_ihs_visit_timestamp,
                     lengths=f"{len(ihs_movements)}, {len(resp_ihs)}, {len(ihs_visits)}"
                     )

        is_update = None

        while len(ihs_visits) > 1 and ihs_visits[0] == ihs_visits[1]:
            self.options['ihs_duplicate'] = True
            ihs_visits = ihs_visits[1:]

        check_for_ihs_updates = \
            IhsUpdateChecks(self.options['check_for_ihs_updates'])
        for ihs, cache_ihs in zip(resp_ihs, ihs_visits):
            cache_ihs['timestamp'] = date2str(str2date(cache_ihs.get('timestamp')))
            cache_ihs['sail_date_full'] = date2str(str2date(cache_ihs.get('sail_date_full')))
            # just check for missing/new entries
            if check_for_ihs_updates in [IhsUpdateChecks.REBUILD_ON_TIMESTAMP,
                                         IhsUpdateChecks.CHECK_BUT_NO_REBUILD,
                                         IhsUpdateChecks.JUST_REBUILD_IHS] and \
                    ihs.get('timestamp') != cache_ihs.get('timestamp'):
                is_update = ihs.get('timestamp')
                logger.debug("ihs", is_update=is_update, cache_ihs=cache_ihs.get('timestamp'))
                break
            # check for any change in the record (strict check)
            if check_for_ihs_updates == IhsUpdateChecks.REBUILD_ON_ITEM and ihs != cache_ihs:
                is_update = ihs.get('timestamp')
                break

        # if IHS data is updated and no need to join with AIS data
        # or check_for_ihs_updates = 4 then just update IHS data in cache
        if is_update and \
                (self.options['ihs_join'] == 0 or check_for_ihs_updates ==
                 IhsUpdateChecks.JUST_REBUILD_IHS) and \
                check_for_ihs_updates != IhsUpdateChecks.CHECK_BUT_NO_REBUILD:
            self.ihs_list_updated = resp_ihs

        return is_update
