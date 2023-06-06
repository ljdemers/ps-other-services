"""Screening Workers ship movement checks module"""
from datetime import datetime, timedelta
import logging
import concurrent.futures

from screening_workers.lib.utils import str2date, \
    json_logger, DATE_FORMAT, date2str

from screening_api.screenings.enums import Severity
from screening_api.screenings.models import Screening
from screening_api.screenings_reports.repositories import (
    ScreeningsReportsRepository,
)
from screening_api.screenings.repositories import ScreeningsRepository
from screening_workers.lib.screening.checks import BaseCheck
from screening_workers.ship_movements.ihs_position import IHSPositionLogic

from screening_workers.lib.blacklist import get_port_country_severity
from screening_workers.lib.sis_api.collections import (
    ShipsCollection, IhsMovementCollection,
)

log = logging.getLogger(__name__)


def _get_ports_from_positions(blacklisted_ports, positions) -> list:
    """ Get the list of port visits and severities from AIS / IHS positions.
    Loop through positions and see if the (lat, lon) is within a port's
    boundary.
    Also check the severity of a port to reduce the amount of times
    we loop over positions.
    Args:
        positions (list): AIS and IHS positions.
    Returns:
        list: List of dicts containing port call information.
    """
    port_visits = []
    last_port = {}
    for position in positions:
        if not (position['latitude'] and position['longitude']):
            # Sometimes IHS doesn't provide us with a latitude or a
            # longitude.
            continue

        if position['port']['port_code'] != '0':
            closest_port = position['port']
        else:
            closest_port = None

        if closest_port and not last_port:
            bl_port = get_port_country_severity(
                blacklisted_ports,
                closest_port['port_name'],
                closest_port['port_country_name'])
            last_port = {
                'port': closest_port,
                'entered': position['timestamp'],
                'departed': position.get('sail_date_full'),
                'severity': bl_port.get('severity'),
                'category': bl_port.get('category')
            }
            port_visits.append(last_port)

        elif closest_port and \
                last_port and \
                last_port['port'] != closest_port:
            # If we haven't picked up ``departed`` from IHS's
            # ``sail_date_full`` then set ``departed`` to
            # ``position.timestamp``
            if last_port['departed'] is None:
                last_port['departed'] = position['timestamp']

            bl_port = get_port_country_severity(
                blacklisted_ports,
                closest_port['port_name'],
                closest_port['port_country_name'])
            last_port = {
                'port': closest_port,
                'entered': position['timestamp'],
                'departed': position.get('sail_date_full'),
                'severity': bl_port.get('severity'),
                'category': bl_port.get('category')
            }
            port_visits.append(last_port)

        elif closest_port and \
                last_port and \
                last_port['port'] == closest_port and \
                position.get('sail_date_full') is not None:
            departed = position.get('sail_date_full')
            last_port['departed'] = departed

        elif not closest_port and last_port:
            # If we haven't picked up ``departed`` from IHS's
            # ``sail_date_full`` then set ``departed`` to
            # ``position.timestamp``
            if last_port['departed'] is None:
                last_port['departed'] = position['timestamp']

            # Create a new ``last_port`` dictionary.
            last_port = {}

    return port_visits


class ShipMovementsCheck(BaseCheck):
    name = 'port_visits'

    def __init__(
            self,
            screenings_repository: ScreeningsRepository,
            screenings_reports_repository: ScreeningsReportsRepository,
            ship_movements_repository,
            ships_repository,
            blacklisted_ports,
            sis_client,
            config,
            smh_client,
            ais_client,
            portservice_client, log_level='INFO'
    ):
        super(ShipMovementsCheck, self).__init__(
            screenings_repository, )
        self.ships_repository = ships_repository
        self.blacklisted_ports = blacklisted_ports
        self.screenings_reports_repository = screenings_reports_repository
        self.sis_client = sis_client
        self.config = config
        self.smh_client = smh_client
        self.ais_client = ais_client
        self.portservice_client = portservice_client
        self.logger = json_logger(__name__, level=log_level)
        self.imo_id = None
        self.screening = None
        self.VOYAGE_STOPPED_SPEED = None
        self.DEFAULT_SHIP_MOVEMENT_DAYS = None
        self.START_AIS_LAST_MIDNIGHT = None
        self.DEFAULT_AIS_REPORTING_MINUTES = None
        self.USE_SMH_SERVICE = 0x02  # default use existing engine
        self.USE_AIS_GAP_RATE = 0

    def _get_ports(self, track):
        ports, elp = self.portservice_client.get_ports(track)
        return ports

    def call_smh(self):
        """ Call SMH service using configuration parameters
        Args:

        Returns:
            response dict from the SMH service
        """
        self.logger.info(
            'Calling SMH service (%s, %s, %s, %s)'
            % (self.imo_id, self.DEFAULT_SHIP_MOVEMENT_DAYS,
               self.DEFAULT_AIS_REPORTING_MINUTES,
               self.config.get('USE_SMH_SERVICE_CACHE')
               )
        )
        response_type = 0x07  # response with visits, positions and IHS data
        if self.USE_AIS_GAP_RATE > 0:
            response_type = 0x27  # include AIS reporting gap
        resp = self.smh_client.get_smh(
            self.imo_id,
            end_date=self.DEFAULT_SHIP_MOVEMENT_DAYS,
            request_days=self.DEFAULT_SHIP_MOVEMENT_DAYS,
            overwrite_cache=1,
            ais_rate=self.DEFAULT_AIS_REPORTING_MINUTES,  # in minutes
            ais_last_midnight=self.START_AIS_LAST_MIDNIGHT,
            speed_filter=self.VOYAGE_STOPPED_SPEED,
            ais_gap_rate=self.USE_AIS_GAP_RATE,
            response_type=response_type,
            use_cache=int(self.config.get('USE_SMH_SERVICE_CACHE', 1)),
            save_port_visits=0,
            external_id=self.screening.id)
        return resp

    def process_smh_request(self):
        """ Call SMH service using configuration parameters
        Args:

        Returns:
            tuple containing Visits, IHS data and Positions.
        """
        visits = []
        ais_track = []
        ihs_data = []
        response = {}
        # Use the SMH service
        if self.USE_SMH_SERVICE & 0x01:
            # run in background
            if self.USE_SMH_SERVICE & 0x02:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    executor.submit(self.call_smh)
            else:  # blocking call if Screening SMH is not required
                try:
                    response = self.call_smh()
                    visits = response.get('visits', [])
                    ais_track = response.get('positions', [])
                    ihs_data = response.get('ihs_movement_data', [])
                    error = response.get('metadata', []).get('error')
                    # Add black listed port severity if any
                    for visit in visits:
                        bl_port = get_port_country_severity(
                            self.blacklisted_ports,
                            visit.get('port', {})['port_name'],
                            visit.get('port', {})['port_country_name'])
                        visit['port']['severity'] = bl_port.get('severity')
                        visit['port']['category'] = bl_port.get('category')

                except Exception as exc:
                    error = 'Failed to get SMH results (%s): %s.' \
                            % (self.screening, exc)

                if error:
                    self.logger.error(error)

        self.logger.info(
            "SMH completed", imo_id=self.imo_id,
            screening_id=self.screening.id,
            elapsed=response.get('metadata', {}).get('elapsed_seconds'),
            visits=len(visits),
            ihs_data=len(ihs_data),
            positions=len(ais_track))

        return visits, ihs_data, ais_track

    def process(self, screening: Screening) -> Severity:

        self.DEFAULT_SHIP_MOVEMENT_DAYS = \
            int(self.config.get('DEFAULT_SHIP_MOVEMENT_DAYS', 365))
        self.DEFAULT_AIS_REPORTING_MINUTES = \
            int(self.config.get('DEFAULT_AIS_REPORTING_MINUTES', 60))
        self.START_AIS_LAST_MIDNIGHT = \
            int(self.config.get('START_AIS_LAST_MIDNIGHT', 1))
        self.VOYAGE_STOPPED_SPEED = \
            int(self.config.get('VOYAGE_STOPPED_SPEED', 99))
        self.USE_SMH_SERVICE = \
            int(self.config.get('USE_SMH_SERVICE', 0x01))
        self.USE_AIS_GAP_RATE = self.DEFAULT_AIS_REPORTING_MINUTES

        # Get imo and mmsi
        ship = self.ships_repository.get(id=screening.ship_id)
        self.imo_id = ship.imo_id
        self.screening = screening
        mmsi = ship.mmsi
        if not mmsi:
            ships_collection = ShipsCollection(self.sis_client)
            data = ships_collection.query(imo_id=self.imo_id)
            mmsi = data[0].mmsi

        self.logger.info(f"SMH Engine={self.USE_SMH_SERVICE}",
                         imo_id=self.imo_id, mmsi=mmsi)

        stop_date = None

        # data from SMH service
        visits, ihs_data, ais_track = self.process_smh_request()

        # existing engine - if this flag is set then screening report will be
        # based on the existing engine
        if self.USE_SMH_SERVICE & 0x02:
            # Compute date range for position data
            dt = datetime.utcnow()
            stop_date = dt - timedelta(days=self.DEFAULT_SHIP_MOVEMENT_DAYS)
            start_date = dt
            if self.START_AIS_LAST_MIDNIGHT == 1:
                start_date = str2date(date2str(dt, DATE_FORMAT))

            # Get IHS movement data
            ship_movement = IhsMovementCollection(self.sis_client)
            try:  # support new SIS movement data ordering
                ihs_data = ship_movement.query(imo_id=self.imo_id, limit=500,
                                               order_by='-timestamp')
            except Exception:
                # backward compatible if ordering is not supported
                ihs_data = ship_movement.query(imo_id=self.imo_id, limit=500)

            # Filtering/dictionizing IHS movement data
            ihs_positions = []
            for pos in ihs_data:
                if pos.entered > stop_date:
                    ihs_positions.append(pos.position_dict())

            # Get AIS positions
            track = None
            filtered = []
            if mmsi:
                track = self.ais_client.get_all_track(
                    mmsi, position_count=500, stop_date=stop_date)

                if not track:
                    log.warning("No AIS Positions found for MMSI %s", mmsi)
                    self.logger.info("No AIS Positions found", mmsi=mmsi)
                    track = None
            else:
                log.warning("No MMSI found for IMO %s", self.imo_id)
                self.logger.info(
                    "No MMSI found", ship=screening.ship_id,
                    imo=str(self.imo_id))

            if track:
                # message rate adjustment
                index = 1
                miss = 0
                latest = track[0]  # latest AIS position
                filtered = []
                latest_ts = str2date(latest.get('timestamp'))
                for pos in track:
                    ts = str2date(pos.get('timestamp'))
                    diff = (latest_ts - ts).total_seconds()
                    if diff >= self.DEFAULT_AIS_REPORTING_MINUTES * 60 and \
                            start_date >= ts >= stop_date:
                        filtered.append(pos)
                        latest_ts = ts
                    else:
                        miss += 1

                    index += 1

                # speed filtering
                if self.VOYAGE_STOPPED_SPEED < 99:  # no filtering if disable
                    filtered = [pos for pos in filtered
                                if not pos['speed'] or pos['speed'] <
                                self.VOYAGE_STOPPED_SPEED]

            # Join AIS and IHS data and sort by timestamp
            filtered.extend(ihs_positions)

            positions = []
            if len(filtered) > 0:
                track = sorted(filtered, key=lambda post: post['timestamp'])

                # get ports for all positions using port service
                ports = self._get_ports(track)

                # Attach port info to positions
                for a, b in zip(track, ports):
                    d = a.copy()
                    d.update({'port': b})
                    positions.append(d)

            # finally compute port visits
            visits = _get_ports_from_positions(self.blacklisted_ports,
                                               positions)
            visits.reverse()

        # Compute port areas visited Severity (either from SMH or this engine)
        port_visits_severity = Severity.OK
        for port in visits:
            severity = port.get('port', {}).get('severity') or Severity.OK
            port_visits_severity = max(port_visits_severity, severity)
            if port.get('entered'):
                port['entered'] = date2str(str2date(port['entered']))
            if port.get('departed'):
                port['departed'] = date2str(str2date(port['departed']))

            p = port.pop('port')
            p['severity'] = severity.name
            p['port_latitude'] = str(p.get('port_latitude') or 90)
            p['port_longitude'] = str(p.get('port_longitude') or 180)

            port.update(p)

        # Compute IHS movement data Severity
        ihs_check = IHSPositionLogic(
            self.portservice_client, self.blacklisted_ports,
            convert_ihs_data=self.USE_SMH_SERVICE & 0x01)
        ihs_movement_severity, ihs_movements = \
            ihs_check.process_ihs_positions(ihs_data, stop_date)

        self.logger.info(
            "All SMH checks completed!",
            visits=port_visits_severity,
            count_visits=len(visits),
            ihs=ihs_movement_severity,
            count_ihs=len(ihs_data),
            ship=screening.ship_id,
            imo=str(self.imo_id),
            USE_SMH_SERVICE=self.USE_SMH_SERVICE
        )

        # Record 'visits' and 'ihs_movements' in
        # screening report repository
        movement_data = {
            "port_visits": visits,
            "ihs_movement_data": ihs_movements
        }
        data = {self.name: movement_data}
        self.logger.debug(data=data)

        session = self.screenings_reports_repository.get_session()
        report, _ = self.screenings_reports_repository.get_or_create(
            screening_id=screening.id,
            create_kwargs={'ship_movements': {}, },
            session=session
        )

        if data:
            self.screenings_reports_repository.update(
                report, **data, session=session)

        self.logger.info("SMH Data/Severity recorded",
                         visits=port_visits_severity,
                         ihs=ihs_movement_severity)

        return max(port_visits_severity, ihs_movement_severity)


class ZoneVisitsCheck(BaseCheck):
    name = 'zone_visits'

    def process(self, screening: Screening) -> Severity:
        # @todo: implement
        return Severity.OK
