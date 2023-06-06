from freezegun import freeze_time
import json
import os
from unittest.mock import patch

from smh_service.smh import get_port_visit_data


@freeze_time('2022-08-10 00:00:00')
class TestSMHOptions:

    @classmethod
    def get_smh_result_options(cls, options):
        os.environ['DEFAULT_DOWNSAMPLE_FREQUENCY_SECONDS'] = '600'
        _, _, _, _, _, _, error, _, options, _, _, _, _, _, _ = \
            get_port_visit_data("", options=options)
        return error, options

    @patch('api_clients.sis.SisClient.get_ship_by_imo')
    def test_get_port_visit_data_with_default_downsample_frequency(self, mock_sis_client):
        options = {'user': 'system', }

        mock_sis_client.return_value = {'mmsi': '123456789'}
        error, options = self.get_smh_result_options(options)

        assert options['downsample_frequency_seconds'] == 600
        # check other defaults
        assert options['ais_days'] == 30
        assert options['rates'] == [10, 60, 120, 240, 1440, 3600]
        assert options['speed_filters'] == {'10': 1, '60': 1, '120': 1, '240': 99,
                                            '1440': 99, '3600': 99}
        assert options['ihs_joins'] == {'10': 1, '60': 1, '120': 1, '240': 1,
                                        '1440': 1, '3600': 1}

    def test_get_port_visit_data_with_requested_downsample_frequency(self):
        downsample_frequency_seconds = 3600  # requested value
        options = {'user': 'system', 'downsample_frequency_seconds': downsample_frequency_seconds}

        error, options = self.get_smh_result_options(options)

        assert options['downsample_frequency_seconds'] == downsample_frequency_seconds

    def test_get_port_visit_data_with_disbaled_requested_downsample_frequency(self):
        downsample_frequency_seconds = 0  # requested value to disable
        options = {'user': 'system', 'downsample_frequency_seconds': downsample_frequency_seconds}
        error, options = self.get_smh_result_options(options)

        assert options['downsample_frequency_seconds'] == downsample_frequency_seconds

    def test_get_port_visit_data_with_user_disabled_downsample(self):
        options = {'user': 'pt', }  # this user is not enabled to use downsampling
        error, options = self.get_smh_result_options(options)

        assert options['downsample_frequency_seconds'] is None

    def test_get_port_visit_data_with_all_user_enabled_downsample(self):
        options = {'user': 'pt', }
        os.environ['DOWNSAMPLE_USER_LIST'] = 'All'
        error, options = self.get_smh_result_options(options)

        assert options['downsample_frequency_seconds'] == 600


if __name__ == '__main__':
    t = TestSMHOptions()

    t.test_get_port_visit_data_with_default_downsample_frequency()
    t.test_get_port_visit_data_with_requested_downsample_frequency()
    t.test_get_port_visit_data_with_user_disabled_downsample()
    t.test_get_port_visit_data_with_all_user_enabled_downsample()
    t.test_get_port_visit_data_with_disbaled_requested_downsample_frequency()

