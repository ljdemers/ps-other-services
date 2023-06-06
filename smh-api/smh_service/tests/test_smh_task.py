import copy
import pytest
from freezegun import freeze_time
from datetime import datetime, timedelta, timezone
import json
import os
from unittest.mock import patch

from api_clients.base_client import ResponseDict
from api_clients.utils import str2date, date2str, ZIPJSON_KEY

from smh_service.smh_task import SMHTask
from smh_service.smh import compute_ais_gaps
from smh_service.tests.helpers import ihs_item, gap_item, smh_data, visit_data, ais_position_item

from flask import Flask


class JsonResp:
    data = None
    status_code = 200

    def __init__(self, data):
        self.data = json.dumps(data).encode()


@freeze_time('2020-08-10 00:00:00')
class TestSMHTask:
    smh_task = None
    app = None
    gaps = []
    mock_ihs_movement = []

    def create_app(self):  # for testing

        app = Flask(__name__)
        app.config['TESTING'] = True
        return app

    def setup(self):

        os.environ['SIS_API_KEY'] = 'xxxx'

        self.app = self.create_app()
        options = {'ihs_join': 1, 'use_cached_positions': False,
                   'eez_rate': 0, 'check_for_ihs_updates': 1}

        imo_number = '123'
        self.gaps = [gap_item(current_report_timestamp=None,
                              last_report_timestamp='2020-06-04T12:56:40Z',
                              gap_hours=532.368),
                     gap_item(current_report_timestamp='2020-06-03T22:32:56Z',
                              current_report_gps=(27.916666, -92.610001),
                              last_report_timestamp='2020-06-03T19:11:50Z',
                              last_report_gps=(27.804455, -91.923828), gap_hours=3.352
                              ),
                     gap_item(current_report_timestamp='2020-06-03T19:11:50Z',
                              current_report_gps=(27.804455, -91.923828),
                              last_report_timestamp='2020-06-03T13:23:57Z',
                              last_report_gps=(27.763334, -90.708336), gap_hours=5.798
                              )
                     ]

        self.mock_ihs_movement = ResponseDict(
            count=3,
            objects=[
                ihs_item(timestamp="2019-12-26T21:50:49", sail_date_full="2020-01-06T11:56:12",
                         latitude="35.029917", longitude="136.850783"),
                ihs_item(timestamp="2020-02-14T16:43:49", sail_date_full="2020-02-17T17:59:25",
                         port_name="San Pedro (Cote d'Ivoire)",
                         latitude="4.734900", longitude="-6.611617"),
                ihs_item(timestamp="2020-03-14T16:43:49", sail_date_full="2020-03-17T17:59:25",
                         port_name="San Pedro",
                         latitude="4.7349", longitude="-6.6116"),
            ]
        )
        self.smh_task = SMHTask(imo_number, options)

    def test_gaps_ongoing(self):
        # last SMH results
        ais_days = 30
        last_smh = {'options': {'smh_count': 2, 'ais_days': ais_days},
                    'ais_gaps': copy.deepcopy(self.gaps)}
        self.smh_task.new_visits = {}
        self.smh_task.new_positions = {}
        self.smh_task.cached_datetime = str2date('2020-06-26T13:23:57Z')
        new_gap = gap_item(current_report_timestamp='2020-06-26T12:56:40Z',
                           last_report_timestamp='2020-06-04T12:56:40Z',
                           last_report_gps=(29.915585, -93.889038))

        self.smh_task.gaps_list = [new_gap]
        self.smh_task.update_cache(last_smh)

        assert len(self.smh_task.gaps_list) == 3
        assert self.smh_task.gaps_list[0] == new_gap
        assert self.smh_task.options['ais_days'] >= ais_days
        assert self.smh_task.options['smh_count'] > last_smh['options']['smh_count']

    def test_gaps_append(self):
        # last SMH results
        ais_days = 30
        self.gaps[0]['current_report'] = {'timestamp': '2020-06-20T10:56:40Z'}
        self.gaps[0]['current_report_timestamp'] = '2020-06-20T10:56:40Z'
        last_smh = {'options': {'smh_count': 1, 'ais_days': ais_days}, 'ais_gaps': self.gaps}

        self.smh_task.cached_datetime = str2date('2020-06-26T13:23:57Z')
        new_gap = gap_item(current_report_timestamp='2020-06-26T12:56:40Z',
                           last_report_timestamp='2020-06-04T12:56:40Z',
                           last_report_gps=(29.915585, -93.889038))

        self.smh_task.gaps_list = [new_gap]
        self.smh_task.update_cache(last_smh)

        assert len(self.smh_task.gaps_list) == 4
        assert self.smh_task.gaps_list[0] == new_gap
        assert self.smh_task.options['smh_count'] > last_smh['options']['smh_count']

    def test_compute_gaps(self):
        last = {'course': 322.0, 'heading': None, 'latitude': 27.916666, 'longitude': -92.610001,
                'mmsi': 366843420, 'source': 'T', 'speed': 1.1, 'status': None,
                'timestamp': '2020-06-10T12:56:40Z'}
        # last position and new positions have > 3 days gap
        new_positions = [
            {'course': 322.0, 'heading': None, 'latitude': 27.91666, 'longitude': -92.6100,
             'mmsi': 366843420, 'source': 'T', 'speed': 1.2, 'status': None,
             'timestamp': '2020-06-13T22:32:56Z'},
            {'course': 325.0, 'heading': None, 'latitude': 27.91666, 'longitude': -92.6100,
             'mmsi': 366843420, 'source': 'T', 'speed': 1.3, 'status': None,
             'timestamp': '2020-06-14T23:32:56Z'}
        ]  # positions have 25 hours gap

        gaps_list, elapsed, error = compute_ais_gaps(new_positions,
                                                     last, ais_threshold=3, get_port=0)

        assert len(gaps_list) == 3

        # The latest gap will always be on-going
        assert gaps_list[0]['current_report_timestamp'] is None
        assert gaps_list[1]['gap_hours'] == 25.0
        assert gaps_list[2]['gap_hours'] >= 72.0

    def test_compute_gaps_remove_older_gaps(self):
        old = {'course': 322.0, 'heading': None, 'latitude': 27.916666, 'longitude': -92.610001,
                'mmsi': 366843420, 'source': 'T', 'speed': 1.1, 'status': None,
                'timestamp': '2020-06-09T12:56:40Z'}
        # last position in cache
        last = {'course': 322.0, 'heading': None, 'latitude': 27.916666, 'longitude': -92.610001,
                'mmsi': 366843420, 'source': 'T', 'speed': 1.1, 'status': None,
                'timestamp': '2020-06-10T12:56:40Z'}

        # have older positions also - should be ignored for gap calculation
        new_positions = [old, last,
            {'course': 322.0, 'heading': None, 'latitude': 27.91666, 'longitude': -92.6100,
             'mmsi': 366843420, 'source': 'T', 'speed': 1.2, 'status': None,
             'timestamp': '2020-06-13T22:32:56Z'},
            {'course': 325.0, 'heading': None, 'latitude': 27.91666, 'longitude': -92.6100,
             'mmsi': 366843420, 'source': 'T', 'speed': 1.3, 'status': None,
             'timestamp': '2020-06-14T23:32:56Z'}
        ]

        gaps_list, elapsed, error = compute_ais_gaps(new_positions,
                                                     last, ais_threshold=3, get_port=0)

        assert len(gaps_list) == 3

        # The latest gap will always be on-going
        assert gaps_list[0]['current_report_timestamp'] is None

    @patch('api_clients.sis.SisClient.get')
    def test_no_ihs_update(self, mock_base_client):
        self.smh_task.options['check_for_ihs_updates'] = 1
        mock_base_client.return_value = self.mock_ihs_movement
        ihs_visits = [ihs_item(timestamp="2019-12-26T21:50:49",
                               sail_date_full="2020-01-06T11:56:12",
                               latitude=35.029917, longitude=136.850783, type='IHS')]

        is_update = self.smh_task.check_for_ihs_update(366, ihs_visits)
        assert not is_update

    @patch('api_clients.sis.SisClient.get')
    def test_no_ihs_update_strict(self, mock_base_client):
        self.smh_task.options['check_for_ihs_updates'] = 2
        mock_base_client.return_value = self.mock_ihs_movement
        ihs_visits = [ihs_item(timestamp="2019-12-26T21:50:49",
                               sail_date_full="2020-01-06T11:56:12",
                               latitude=35.029917, longitude=136.850783, type='IHS')]

        is_update = self.smh_task.check_for_ihs_update(366, ihs_visits)
        assert not is_update

    @patch('api_clients.sis.SisClient.get')
    def test_no_ihs_update_strict_failed(self, mock_base_client):
        # There is no new record but data change in updated IHS
        self.smh_task.options['check_for_ihs_updates'] = 2
        mock_base_client.return_value = self.mock_ihs_movement
        ihs_visits = [ihs_item(timestamp="2019-12-26T21:50:49", port_name="Nagoya 2",  # change
                               sail_date_full="2020-01-06T11:56:12",
                               latitude=35.029917, longitude=136.850783, type='IHS')]

        is_update = self.smh_task.check_for_ihs_update(366, ihs_visits)
        assert is_update

    @patch('api_clients.sis.SisClient.get')
    def test_ihs_update(self, mock_base_client):
        # A new middle record which was not in cache
        self.smh_task.options['check_for_ihs_updates'] = 1
        mock_base_client.return_value = self.mock_ihs_movement
        ihs_visits = [
            ihs_item(timestamp="2020-03-14T16:43:49", sail_date_full="2020-03-17T17:59:25",
                     port_name="San Pedro",
                     latitude=4.7349, longitude=-6.6116, type='IHS'),
            ihs_item(timestamp="2019-12-26T21:50:49",
                     sail_date_full="2020-01-06T11:56:12",
                     latitude=35.029917, longitude=136.850783, type='IHS')
        ]

        is_update = self.smh_task.check_for_ihs_update(366, ihs_visits)
        assert is_update

        # same as self.smh_task.options['check_for_ihs_updates'] = 1
        self.smh_task.options['check_for_ihs_updates'] = 3
        is_update = self.smh_task.check_for_ihs_update(366, ihs_visits)
        assert is_update

        # strict
        self.smh_task.options['check_for_ihs_updates'] = 2
        is_update = self.smh_task.check_for_ihs_update(366, ihs_visits)
        assert is_update

    @patch('api_clients.sis.SisClient.get')
    def test_ihs_update_no_data(self, mock_base_client):
        # Returns False if no IHS data
        self.smh_task.options['check_for_ihs_updates'] = 1

        # no IHS movement data but some in cache
        mock_base_client.return_value = ResponseDict(count=1, objects=[])
        ihs_visits = [ihs_item(timestamp="2019-12-26T21:50:49",
                               sail_date_full="2020-01-06T11:56:12",
                               latitude=35.029917, longitude=136.850783, type='IHS')]
        is_update = self.smh_task.check_for_ihs_update(366, ihs_visits)
        assert not is_update

        # no cached IHS
        mock_base_client.return_value = self.mock_ihs_movement
        is_update = self.smh_task.check_for_ihs_update(366, [{}])
        assert not is_update

        # return false also if this check is disabled
        self.smh_task.options['check_for_ihs_updates'] = 0
        is_update = self.smh_task.check_for_ihs_update(366, ihs_visits)
        assert not is_update

        assert datetime.utcnow().day == 10

    @patch('api_clients.sis.SisClient.get')
    def test_ihs_update_no_cache_rebuild(self, mock_base_client):
        # A new middle record which was not in cache but just update IHS in cache
        self.smh_task.options['check_for_ihs_updates'] = 4
        mock_base_client.return_value = self.mock_ihs_movement
        ihs_visits = [
            ihs_item(timestamp="2020-03-14T16:43:49", sail_date_full="2020-03-17T17:59:25",
                     port_name="San Pedro",
                     latitude=4.7349, longitude=-6.6116, type='IHS'),
            ihs_item(timestamp="2019-12-26T21:50:49",
                     sail_date_full="2020-01-06T11:56:12",
                     latitude=35.029917, longitude=136.850783, type='IHS')
        ]

        is_update = self.smh_task.check_for_ihs_update(366, ihs_visits)
        assert is_update
        assert self.smh_task.ihs_list_updated and len(self.smh_task.ihs_list_updated) == 3

    @patch('smh_service.smh_task.SMHData.get_cached_smh_data')
    def test_get_cached_smh_cache_found_begin_date(self, mock_get_cache):
        """Cache found and will be used"""
        self.smh_task.options['ais_days'] = 0
        mock_get_cache.return_value = smh_data(options={'ais_days': 10},  # 10 days cache
                                               timestamp=str2date('2020-08-05 00:00:00'),)

        self.smh_task.options['use_cache'] = 1
        self.smh_task.options['check_for_ihs_updates'] = 0
        end_date = datetime.utcnow() - timedelta(days=5)
        last_smh, _ = self.smh_task.get_cached_smh(date2str(end_date))
        assert last_smh is not None

        # cache found but it has fewer days of data - so ignore cache and rebuild
        end_date = datetime.utcnow() - timedelta(days=20)
        last_smh, _ = self.smh_task.get_cached_smh(date2str(end_date))
        assert last_smh is None

    @patch('smh_service.smh_task.SMHData.get_cached_smh_data')
    def test_get_cached_smh_cache_found(self, mock_get_cache):
        """Cache found and will be used"""
        mock_get_cache.return_value = smh_data(id=5, timestamp=datetime.utcnow(),
                                               options={'ais_days': 15})  # 15 days cache

        self.smh_task.options['use_cache'] = 1
        self.smh_task.options['ais_days'] = 12
        self.smh_task.options['check_for_ihs_updates'] = 0
        last_smh, _ = self.smh_task.get_cached_smh(None)
        assert last_smh is not None
        assert self.smh_task.options['last_smh_id'] == 5

        # cache found but it has fewer days of data - so ignore cache and rebuild
        self.smh_task.options['ais_days'] = 20
        last_smh, cached_positions = self.smh_task.get_cached_smh(None)
        assert last_smh is None
        assert cached_positions == {}

    @patch('smh_service.smh_task.SMHData.get_cached_smh_data')
    def test_get_cached_smh_new_format_cache_found(self, mock_get_cache):
        """Cache found and will be used"""
        mock_get_cache.return_value = smh_data(update_count=1, id=1,
                                               timestamp=datetime.utcnow(),
                                               options={'ais_days': 15})  # 15 days cache

        self.smh_task.options['use_cache'] = 1
        self.smh_task.options['ais_days'] = 12
        self.smh_task.options['check_for_ihs_updates'] = 0
        last_smh, _ = self.smh_task.get_cached_smh(None)
        assert last_smh is not None
        assert self.smh_task.options['last_smh_id'] == 1

        # cache found but it has fewer days of data - so ignore cache and rebuild
        self.smh_task.options['ais_days'] = 20
        last_smh, _ = self.smh_task.get_cached_smh(None)
        assert last_smh is None

    @patch('smh_service.smh_task.SMHData.get_cached_smh_data')
    def test_get_cached_smh_exception(self, mock_get_cache):
        """Any exception means no cache to read i.e. perform a new SMH"""

        mock_get_cache.return_value = smh_data()

        self.smh_task.options['use_cache'] = 1
        self.smh_task.options['check_for_ihs_updates'] = 0
        end_date = datetime.utcnow() - timedelta(days=5)
        last_smh, _ = self.smh_task.get_cached_smh(end_date)

        assert last_smh is None

    @patch('smh_service.smh_task.SMHData.get_cached_smh_data')
    def test_get_cached_smh_no_cache_found(self, mock_get_cache):
        """No cache found for the IMO """

        mock_get_cache.return_value = smh_data()  # no cache

        self.smh_task.options['use_cache'] = 1
        self.smh_task.options['check_for_ihs_updates'] = 0
        end_date = datetime.utcnow() - timedelta(days=5)
        last_smh, _ = self.smh_task.get_cached_smh(date2str(end_date))

        assert last_smh is None

    @patch('smh_service.smh_task.SMHData.get_cached_smh_data')
    def test_get_cached_smh_use_no_cache(self, mock_get_cache):
        """Cache rebuild with use_cache=0, cache may or may not exist """

        mock_get_cache.return_value = smh_data(options={}, timestamp=datetime.utcnow())
        self.smh_task.options['use_cache'] = 0
        self.smh_task.options['check_for_ihs_updates'] = 0
        end_date = datetime.utcnow() - timedelta(days=5)
        last_smh, _ = self.smh_task.get_cached_smh(date2str(end_date))
        assert last_smh == {}

    @patch('smh_service.smh_task.SMHTask.check_for_ihs_update')
    @patch('smh_service.smh_task.SMHData.get_cached_smh_data')
    def test_get_cached_smh_cache_rebuilt_ihs_updated(self, mock_get_cache, mock_ihs_update):
        """Cache rebuild as IHS data is updated """

        mock_get_cache.return_value = smh_data(options={'ais_days': 15},
                                               timestamp=datetime.utcnow(),
                                               ihs=[ihs_item()])
        mock_ihs_update.return_value = True

        self.smh_task.options['use_cache'] = 1
        self.smh_task.options['ais_days'] = 12
        self.smh_task.options['check_for_ihs_updates'] = 1
        last_smh, _ = self.smh_task.get_cached_smh(None)
        assert last_smh is None  # ignore cached data
        assert self.smh_task.options['ihs_updated'] is True

    @patch('smh_service.smh_task.SMHTask.check_for_ihs_update')
    @patch('smh_service.smh_task.SMHData.get_cached_smh_data')
    def test_get_cached_smh_no_cache_rebuilt_ihs_updated(self, mock_get_cache, mock_ihs_update):
        """No Cache rebuild but IHS data is updated (just mark it) """

        mock_get_cache.return_value = smh_data(options={'ais_days': 15},
                                               timestamp=datetime.utcnow(),
                                               ihs=[ihs_item()])
        mock_ihs_update.return_value = True

        self.smh_task.options['use_cache'] = 1
        self.smh_task.options['ihs_join'] = 1
        self.smh_task.options['ais_days'] = 12
        self.smh_task.options['check_for_ihs_updates'] = 3
        last_smh, _ = self.smh_task.get_cached_smh(None)
        assert last_smh is not None  # keep cached data
        assert self.smh_task.options['ihs_updated'] is True

    @patch('smh_service.smh_task.SMHTask.check_for_ihs_update')
    @patch('smh_service.smh_task.SMHData.get_cached_smh_data')
    def test_get_cached_smh_no_cache_rebuilt_ihs_updated_no_ihs_join(self, mock_get_cache,
                                                                     mock_ihs_update):
        """No Cache rebuild but IHS data is updated (just mark it) """

        mock_get_cache.return_value = smh_data(options={'ais_days': 15},
                                               timestamp=datetime.utcnow(),
                                               ihs=[ihs_item()])
        mock_ihs_update.return_value = True

        self.smh_task.options['use_cache'] = 1
        self.smh_task.options['ais_days'] = 12
        self.smh_task.options['ihs_join'] = 0
        self.smh_task.options['check_for_ihs_updates'] = 1
        last_smh, _ = self.smh_task.get_cached_smh(None)
        assert last_smh is not None  # keep cached data
        assert self.smh_task.options['ihs_updated'] is True

        self.smh_task.options['check_for_ihs_updates'] = 4 # no cache rebuild - just uodate IHS
        self.smh_task.options['ihs_join'] = 1
        last_smh, _ = self.smh_task.get_cached_smh(None)
        assert last_smh is not None  # keep cached data
        assert self.smh_task.options['ihs_updated'] is True

    @patch('smh_service.smh_task.SMHTask.check_for_ihs_update')
    @patch('smh_service.smh_task.SMHData.get_cached_smh_data')
    def test_get_cached_smh_use_cached_positions(self, mock_get_cache, mock_ihs_update):
        """Use cached positions for building cache """

        mock_get_cache.return_value = smh_data(options={'ais_days': 15},
                                               timestamp=datetime.utcnow(),
                                               positions={
                                                   '3600': [ais_position_item(), ihs_item()]},
                                               visits={'3600': [visit_data(),
                                                                visit_data(
                                                                    entered="2020-08-05T20:14:20Z",
                                                                    departed="2020-08-09T20:14:20Z",
                                                                    type='Moored')
                                                                ]
                                                       }
                                               )
        mock_ihs_update.return_value = False

        self.smh_task.options['use_cache'] = 1
        self.smh_task.options['ais_days'] = 12
        self.smh_task.options['use_cached_positions'] = True
        self.smh_task.options['check_for_ihs_updates'] = 1
        last_smh, cached_positions = self.smh_task.get_cached_smh(None)
        assert last_smh is not None  # keep cached data
        assert len(cached_positions['3600']) == 2  # extract positions from cache

    @patch('smh_service.smh_task.SMHTask.check_for_ihs_update')
    @patch('smh_service.smh_task.SMHData.get_cached_smh_data')
    def test_get_cached_smh_with_eez_enabled(self, mock_get_cache, mock_ihs_update):
        """EEZ enabled so rebuild if no EEZ data in cache """

        # no EEZ data in cache (default)
        mock_get_cache.return_value = smh_data(options={'ais_days': 15},
                                               timestamp=datetime.utcnow())
        mock_ihs_update.return_value = False

        self.smh_task.options['use_cache'] = 1
        self.smh_task.options['ais_days'] = 12
        self.smh_task.options['eez_rate'] = 60
        last_smh, _ = self.smh_task.get_cached_smh(None)
        assert last_smh is None  # Cache rebuild

        # EEZ data is cache at a diff. rate (3600 <> 60) - so rebuild also
        mock_get_cache.return_value = smh_data(options={'ais_days': 15, 'eez_rate': 3600})
        last_smh, _ = self.smh_task.get_cached_smh(None)
        assert last_smh is None  # Cache rebuild

        # EEZ data is in cache at same rate - so no rebuild
        mock_get_cache.return_value = smh_data(options={'ais_days': 15, 'eez_rate': 60},
                                               timestamp=datetime.utcnow())
        self.smh_task.options['eez_rate'] = 60
        last_smh, _ = self.smh_task.get_cached_smh(None)
        assert last_smh is not None  # No Cache rebuild

    @patch('smh_service.smh_task.get_port_visit_data')
    def test_get_smh_results_empty(self, mock_get_port_visit_data):
        """ No cache - no SMH results"""
        self.smh_task.end_date = datetime.utcnow() - timedelta(days=5)
        self.smh_task.ihs_list_updated = None
        self.smh_task.options['old_cache'] = 1
        self.smh_task.options['use_cached_positions'] = False
        self.smh_task.options['use_new_cache_table'] = 0
        mock_get_port_visit_data.return_value = ({}, [], {}, {}, {}, None, None, {},
                                                 self.smh_task.options,
                                                 {}, [], [], {}, {}, [])

        self.smh_task.get_smh_results(None, {})

        assert self.smh_task.options['screened_date'] == date2str(datetime.utcnow())
        assert self.smh_task.options['mmsi_count'] == 0
        assert self.smh_task.options['cache_updated'] == 0
        assert self.smh_task.end_date is None

    @patch('smh_service.smh_task.get_port_visit_data')
    def test_get_smh_results_empty_no_cache(self, mock_get_port_visit_data):
        """ some cache - no SMH results but write to new cache"""
        self.smh_task.end_date = datetime.utcnow() - timedelta(days=5)
        self.smh_task.options['use_new_cache_table'] = 1
        mock_get_port_visit_data.return_value = ({}, [], {}, {}, {}, None, None, {},
                                                 self.smh_task.options,
                                                 {}, [], [], {}, {}, [])

        self.smh_task.get_smh_results(smh_data(), {})

        assert self.smh_task.options['screened_date'] == date2str(datetime.utcnow())
        assert self.smh_task.options['mmsi_count'] == 0
        assert self.smh_task.options['cache_updated'] == 0
        assert self.smh_task.new_visits == {} or None

    @patch('smh_service.smh_task.get_port_visit_data')
    def test_get_smh_results_ok(self, mock_get_port_visit_data):
        """ No cache - some SMH results"""
        cached_data = None
        self.smh_task.end_date = datetime.utcnow() - timedelta(days=5)
        visit_dict = {'3600': [visit_data(),
                               visit_data(entered="2020-08-05T20:14:20Z",
                                          departed="2020-08-09T20:14:20Z", type='Moored')
                               ]
                      }
        position_dict = {'3600': [ais_position_item(), ihs_item()]}

        mock_get_port_visit_data.return_value = ({}, self.mock_ihs_movement.objects,
                                                 visit_dict, {}, {}, None, None,
                                                 position_dict, {},
                                                 {'objects': [{'id': 1, 'mmsi': '12345'},
                                                              {'id': 2, 'mmsi': '54321'}]
                                                  },
                                                 self.gaps, [], {}, {}, [])

        self.smh_task.get_smh_results(cached_data, {})

        assert self.smh_task.options['screened_date'] == date2str(datetime.utcnow())
        assert self.smh_task.options['mmsi_count'] == 2
        assert self.smh_task.options['cache_updated'] == 1
        assert 'total_time' in self.smh_task.elapsed
        assert len(self.smh_task.new_positions.get('3600')) == 2
        assert len(self.smh_task.new_visits.get('3600')) == 2
        assert len(self.smh_task.mmsi_history) == 2
        assert self.smh_task.mmsi_history[0].get('mmsi') == '12345'

        """ some cache - some SMH results"""
        cached_data = smh_data()
        self.smh_task.end_date = datetime.utcnow() - timedelta(days=5)
        self.smh_task.get_smh_results(cached_data, {})
        assert self.smh_task.options['cache_updated'] == 1
        assert self.smh_task.end_date is not None

    @patch('smh_service.smh_task.get_port_visit_data')
    def test_get_smh_results_exception(self, mock_get_port_visit_data):
        """ Exception during SMH result computation"""
        self.smh_task.options = {}
        self.smh_task.end_date = datetime.utcnow() - timedelta(days=5)

        mock_get_port_visit_data.return_value = IOError('fail')

        with pytest.raises(Exception):
            self.smh_task.get_smh_results(None, {})

        assert self.smh_task.options.get('error') is not None
        assert 'error' in self.smh_task.options
        assert 'screened_date' not in self.smh_task.options

    @patch('smh_service.smh_task.get_port_visit_data')
    def test_get_smh_results_with_stops(self, mock_get_port_visit_data):
        """ SMH result contains stops"""
        self.smh_task.end_date = datetime.utcnow() - timedelta(days=5)
        self.smh_task.options['use_new_cache_table'] = 1
        self.smh_task.options['detect_stops'] = 1
        stop_call = {'port_name': 'stopped', 'port_code': 'STOPPED', 'port_country_name': 'Stop'}
        stopped_data = visit_data(port=stop_call, type='At anchor')
        mock_get_port_visit_data.return_value = ({}, [], {}, {}, {}, None, None, {},
                                                 self.smh_task.options,
                                                 {}, [], [], {}, {}, [stopped_data])

        self.smh_task.get_smh_results(smh_data(), {})

        assert self.smh_task.options['detect_stops'] == 1
        # one non-port stops
        assert self.smh_task.non_port_stops and len(self.smh_task.non_port_stops)==1
        assert self.smh_task.new_visits == {} or None

    def test_update_cache_without_cache(self):
        """ No cache - some SMH results"""
        cached_data = None
        self.smh_task.cached_datetime = None
        self.smh_task.new_visits = {'3600': [visit_data(),
                                             visit_data(entered="2020-08-05T20:14:20Z",
                                                        departed="2020-08-09T20:14:20Z",
                                                        type='Moored')
                                             ]
                                    }
        self.smh_task.new_positions = {'3600': [ais_position_item(), ihs_item()]}
        self.smh_task.options['screened_date'] = '2020-08-05T00:00:00Z'
        self.smh_task.update_cache(cached_data)

        assert self.smh_task.options['smh_count'] == 1
        assert 'first_smh_timestamp' in self.smh_task.options
        assert len(self.smh_task.visit_list_dict.get('3600')) == 2
        assert len(self.smh_task.position_list_dict.get('3600')) == 2
        assert self.smh_task.options['first_smh_timestamp'] == \
               self.smh_task.options['screened_date']

    def test_update_cache_with_cache(self):
        """ some cache + some new SMH results = Joined data to cache"""
        self.smh_task.new_visits = {'3600': [visit_data(),
                                             visit_data(entered="2020-08-05T20:14:20Z",
                                                        departed="2020-08-09T20:14:20Z",
                                                        type='Moored')
                                             ]
                                    }
        self.smh_task.new_positions = {'3600': [ais_position_item(), ihs_item()]}
        screened_date = datetime.now(timezone.utc) - timedelta(days=5)
        cached_data = smh_data(timestamp=screened_date,
                               options={'smh_count': 8, 'ais_positions_count': 5,
                                        'ais_days': 15, 'ais_gaps_count': 3})
        self.smh_task.cached_datetime = str2date('2020-08-05 00:00:00')  # 5 days old cache
        self.smh_task.options['ais_positions_count'] = 2
        self.smh_task.options['ais_gaps_count'] = 1
        self.smh_task.options['ais_days'] = 20

        self.smh_task.update_cache({'options': cached_data[0]})

        assert len(self.smh_task.visit_list_dict.get('3600')) == 2
        assert len(self.smh_task.position_list_dict.get('3600')) == 2
        assert self.smh_task.options['smh_count'] == 9
        assert self.smh_task.options['ais_gaps_count'] == 4
        assert self.smh_task.options['ais_positions_count'] == 7
        assert self.smh_task.options['ais_days'] == 20
        assert self.smh_task.options['first_smh_timestamp'] == '2020-08-05T00:00:00Z'

    def test_update_cache_with_cache_and_ihs_updated(self):
        """ some cache + some new SMH results + IHS data was back filled = Joined data to cache"""

        self.smh_task.ihs_list = [ihs_item(port_name='ABC')]  # new data
        self.smh_task.visit_list_dict = {'3600': [visit_data(entered="2020-08-05T01:14:20Z",
                                                             departed="2020-08-05T05:14:20Z",
                                                             type='fishing')]}
        self.smh_task.new_visits = {'3600': [visit_data(),
                                             visit_data(entered="2020-08-05T20:14:20Z",
                                                        departed="2020-08-09T20:14:20Z",
                                                        type='Moored')
                                             ]
                                    }
        self.smh_task.new_positions = {'3600': [ais_position_item(), ihs_item()]}

        back_filled_ihs1 = ihs_item(timestamp="2020-03-14T16:43:49",
                                    sail_date_full="2020-03-17T17:59:25",
                                    port_name="San Pedro",
                                    latitude=4.7349, longitude=-6.6116, type='IHS')
        back_filled_ihs2 = ihs_item(timestamp="2019-12-26T21:50:49",
                                    sail_date_full="2020-01-06T11:56:12",
                                    latitude=35.029917, longitude=136.850783, type='IHS')
        # updated IHS data (back filled)
        self.smh_task.ihs_list_updated = [back_filled_ihs1, back_filled_ihs2]

        screened_date = datetime.now(timezone.utc) - timedelta(days=5)
        cached_data = smh_data(timestamp=screened_date,
                               ihs=[ihs_item()],  # cached old/obsolete IHS data
                               options={'smh_count': 8, 'ais_positions_count': 5,
                                        'ais_days': 15, 'ais_gaps_count': 3})

        self.smh_task.cached_datetime = str2date('2020-08-05 00:00:00')  # 5 days old cache
        self.smh_task.options['ais_positions_count'] = 2
        self.smh_task.options['ais_gaps_count'] = 1
        self.smh_task.options['ais_days'] = 20

        self.smh_task.update_cache({'options': cached_data[0], 'ihs': cached_data[3]})

        assert len(self.smh_task.visit_list_dict.get('3600')) == 3
        assert len(self.smh_task.position_list_dict.get('3600')) == 2
        assert len(self.smh_task.ihs_list) == 3
        assert ihs_item() not in self.smh_task.ihs_list  # make sure obsolete data not in cache
        assert ihs_item(port_name='ABC') in self.smh_task.ihs_list  # new data is in cache
        assert back_filled_ihs1 in self.smh_task.ihs_list and \
               back_filled_ihs2 in self.smh_task.ihs_list  # and back-filled data also in cache

    def test_update_cache_with_some_duplicate_calls(self):
        """ some cache + some new SMH results (with older redundant positions and port calls) """
        self.smh_task.new_visits = {'3600': [
            visit_data(entered="2020-08-05T20:14:20Z",
                       departed="2020-08-09T20:14:20Z",
                       type='Moored'),
            visit_data(),
            visit_data(entered="2020-07-25T20:14:20Z",
                       departed="2020-07-27T20:14:20Z")
        ]
        }
        self.smh_task.new_positions = {'3600': [ihs_item(), ais_position_item()]}
        screened_date = datetime.now(timezone.utc) - timedelta(days=5)
        cached_data = smh_data(timestamp=screened_date,
                               visits={'3600': [visit_data(),
                                                visit_data(entered="2020-07-25T20:14:20Z",
                                                           departed="2020-07-27T20:14:20Z")
                                                ]
                                       },
                               positions={'3600': [
                                   ais_position_item(timestamp="2019-12-27T21:50:49"),
                                   ais_position_item()
                               ]
                               },
                               options={'smh_count': 8, 'ais_positions_count': 5,
                                        'ais_days': 15, 'ais_gaps_count': 3})
        self.smh_task.cached_datetime = str2date('2020-08-05 00:00:00')  # 5 days old cache
        self.smh_task.visit_list_dict = cached_data[1]
        self.smh_task.position_list_dict = cached_data[2]
        self.smh_task.update_cache({'options': cached_data[0]})

        # older positions and visits are removed
        assert len(self.smh_task.visit_list_dict.get('3600')) == 3
        assert len(self.smh_task.position_list_dict.get('3600')) == 2

    @patch('smh_service.smh_task.SMHData.insert_update_smh_data')
    def test_cache_results_new_cache(self, mock_insert_to_db):
        """ cache build with new cache table"""
        self.smh_task.options['use_new_cache_table'] = 1
        self.smh_task.options['save_port_visits'] = 0
        self.smh_task.options['last_smh_id'] = 5
        self.smh_task.options['overwrite_cache'] = 0

        self.smh_task.position_list_dict = {'3600': [ais_position_item(), ihs_item()]}
        self.smh_task.visit_list_dict = {'3600': [visit_data(),
                                visit_data(entered="2020-08-05T20:14:20Z",
                                           departed="2020-08-09T20:14:20Z",
                                           type='Moored')
                                ]
                       }

        result = self.smh_task.cache_results(self.app)
        assert result == "smh_data"
        assert mock_insert_to_db.called_once

        # new cache to new cache - upsert if cache exists
        self.smh_task.options['use_new_cache_table'] = 1
        self.smh_task.options['overwrite_cache'] = True
        self.smh_task.options['old_cache'] = 0
        self.smh_task.options['last_update_count'] = 3
        result = self.smh_task.cache_results(self.app)

        positions = mock_insert_to_db.call_args[0][0].get('positions')
        visits = mock_insert_to_db.call_args[0][0].get('port_visits')

        # Upsert in new table
        assert result == "smh_data"
        assert mock_insert_to_db.call_args[0][2]  # True
        assert 'last_update_count' in mock_insert_to_db.call_args[0][0].get('options')
        assert 'positions' in mock_insert_to_db.call_args[0][0]
        assert mock_insert_to_db.call_args[0][1] == 5   # last Id

        assert ZIPJSON_KEY not in positions  # position data is not zipped by default
        assert ZIPJSON_KEY not in visits  # visit data is never zipped

    @patch('smh_service.smh_task.SMHData.insert_update_smh_data')
    def test_cache_results_zip_data(self, mock_insert_to_db):
        """ cache build with some data zipped in DB"""
        self.smh_task.options['use_new_cache_table'] = 1
        self.smh_task.options['save_port_visits'] = 0
        self.smh_task.options['last_smh_id'] = 5
        self.smh_task.options['zip_data'] = True

        self.smh_task.position_list_dict = {'3600': [ais_position_item(), ihs_item()]}
        self.smh_task.ihs_list = ihs_item()
        self.smh_task.visit_list_dict = {'3600': [visit_data(),
                                visit_data(entered="2020-08-05T20:14:20Z",
                                           departed="2020-08-09T20:14:20Z",
                                           type='Moored')
                                ]
                       }
        self.smh_task.gaps_list = gap_item()

        result = self.smh_task.cache_results(self.app)

        positions = mock_insert_to_db.call_args[0][0].get('positions')
        visits = mock_insert_to_db.call_args[0][0].get('port_visits')
        ihs_movements = mock_insert_to_db.call_args[0][0].get('ihs_movements')
        gaps = mock_insert_to_db.call_args[0][0].get('ais_gaps')

        assert 'positions' in mock_insert_to_db.call_args[0][0]
        assert 'zip_data' in mock_insert_to_db.call_args[0][0].get('options')
        assert mock_insert_to_db.call_args[0][0].get('options').get('zip_data')  # True
        assert ZIPJSON_KEY in positions  # position data is zipped
        assert ZIPJSON_KEY in ihs_movements[0]  # IHS data is zipped as an array of length 1
        assert ZIPJSON_KEY in gaps[0]  # gap data is zipped as an array of length 1
        assert ZIPJSON_KEY not in visits  # visit data is never zipped


if __name__ == '__main__':
    t = TestSMHTask()
    t.setup()

    t.test_gaps_ongoing()
    t.test_gaps_append()
    t.test_compute_gaps()
    t.test_compute_gaps_remove_older_gaps()

    t.test_no_ihs_update()
    t.test_no_ihs_update_strict()
    t.test_no_ihs_update_strict_failed()
    t.test_ihs_update()
    t.test_ihs_update_no_data()
    t.test_ihs_update_no_cache_rebuild()

    t.test_get_cached_smh_cache_found_begin_date()
    t.test_get_cached_smh_cache_found()
    t.test_get_cached_smh_exception()
    t.test_get_cached_smh_use_no_cache()
    t.test_get_cached_smh_no_cache_found()
    t.test_get_cached_smh_new_format_cache_found()
    t.test_get_cached_smh_cache_rebuilt_ihs_updated()
    t.test_get_cached_smh_no_cache_rebuilt_ihs_updated()
    t.test_get_cached_smh_no_cache_rebuilt_ihs_updated_no_ihs_join()
    t.test_get_cached_smh_use_cached_positions()
    t.test_get_cached_smh_with_eez_enabled()

    t.test_get_smh_results_empty()
    t.test_get_smh_results_empty_no_cache()
    t.test_get_smh_results_ok()
    t.test_get_smh_results_exception()
    t.test_get_smh_results_with_stops()

    t.test_update_cache_with_cache()
    t.test_update_cache_without_cache()
    t.test_update_cache_with_cache_and_ihs_updated()
    t.test_update_cache_with_some_duplicate_calls()

    t.test_cache_results_new_cache()
    t.test_cache_results_zip_data()
