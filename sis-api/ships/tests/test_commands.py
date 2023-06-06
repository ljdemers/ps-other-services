from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytz
from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import TestCase

from ships.models import CompanyHistory, FlagHistory, ShipDataHistory
from ships.models.company_history import CompanyAssociationTypes
from ships.tests.factories import (CompanyHistoryFactory, FlagHistoryFactory,
                                   ShipDataHistoryFactory)
from ships.utils import get_first, get_last
from ships.utils.company_history import (UNKNOWN_COMPANY_CODE,
                                         UNKNOWN_COMPANY_NAME)


class TestImportShipDataHistoryCommand(TestCase):
    def setUp(self):
        self.imos = [
            '1007249',
            '1007548',
            '1007641',
            '1007615',
            '1003308',
            '1006673',
            '1003308',
            '1006556',
            '1006673',
        ]
        self.path = Path(settings.PROJECT_ROOT) / 'ships' / 'tests' / 'data'
        self.path_without_csvs = Path(settings.PROJECT_ROOT) / 'system'

    def test_import_ship_data_history_without_csvs(self):
        # Given: all required arguments to import_ship_data_history command
        # with a path that doesn't contain CSV files.
        expected_message = 'No files were matched against such pattern: *ShipData.CSV'

        # When: a command launches with arguments.
        with self.assertRaises(CommandError) as exc:
            call_command(
                'import_ship_data_history',
                path=str(self.path_without_csvs),
            )

        message = exc.exception.args[0]

        # Then: it throws an error there aren't any files.
        assert expected_message in message

    def test_import_ship_data_history_with_wrong_path(self):
        # Given: all required arguments to import_ship_data_history command
        # with a wrong path.
        expected_message = 'There is no such path /usr/src/app/system/wrong'

        # When: a command launches with arguments.
        with self.assertRaises(CommandError) as exc:
            call_command(
                'import_ship_data_history',
                path=str(self.path_without_csvs / 'wrong'),
            )

        message = exc.exception.args[0]

        # Then: it throws an error there is no such path exists.
        assert expected_message in message

    @patch('ships.utils.ship_history.logger')
    def test_import_ship_data_history_from_csv(self, mock_logger):
        # Given: all required arguments to import_ship_data command.
        # When: a command launches with arguments.
        call_command(
            'import_ship_data_history',
            path=str(self.path),
        )

        entries = ShipDataHistory.objects.filter(imo_id__in=self.imos)

        # Then: it shows a success message about creation of entries.
        assert mock_logger.mock_calls
        assert entries.count() == len(self.imos)

    def test_import_existing_ship_data_history(self):
        # Given: all required arguments to import_ship_data command.
        output = StringIO()

        # When: a command launches with arguments.
        call_command(
            'import_ship_data_history',
            path=str(self.path),
            stdout=StringIO(),  # don't cause exit code 1
        )

        # And: 2nd run happens for the same files.
        call_command(
            'import_ship_data_history',
            path=str(self.path),
            stdout=output,
        )

        entries = ShipDataHistory.objects.filter(imo_id__in=self.imos)
        message = 'Data imported successfully'

        # Then: a success message shown but existing data not imported twice.
        assert entries.count() == len(self.imos)
        assert message in output.getvalue()

    def test_import_ship_data_history_with_empty_build_year(self):
        # Given: Required arguments to import_ship_data command.
        output = StringIO()
        ship_name = 'ASOLARE'

        # When: a command launches with arguments.
        call_command(
            'import_ship_data_history',
            path=str(self.path),
            stdout=output,
        )

        message = 'Data imported successfully'
        entries = ShipDataHistory.objects.filter(imo_id__in=self.imos)
        ship = entries.get(ship_name=ship_name)

        # Then: it creates an entry that contains empty build year.
        assert ship
        assert not ship.year_of_build
        assert message in output.getvalue()
        assert len(entries) == len(self.imos)

    def test_populate_flag_history(self):
        """Test populate flag history positive case."""
        num_records = 10
        ShipDataHistoryFactory.create_batch(size=num_records)

        with self.assertLogs() as captured:
            call_command(
                'flaghistory',
                'populate',
            )
            assert captured.output == [
                'INFO:management:Populating flag history...',
                f'INFO:management:{num_records}/{num_records} done',
                f'INFO:management:{num_records} flag history records created successfully.',
                'WARNING:management:0 flag history records marked as ignored.',
            ]

        assert num_records == FlagHistory.objects.count()

    def test_populate_flag_history_with_empty_ship_data(self):
        """Test populate flag history with no ship data positive case."""
        with self.assertLogs() as captured:
            call_command(
                'flaghistory',
                'populate',
            )

            assert captured.output == [
                'INFO:management:Populating flag history...',
                'ERROR:management:No flag history records created.',
            ]

        assert FlagHistory.objects.count() == 0

    def test_populate_flag_history_with_full_batch(self):
        """Test populate flag history with full batch of ship history objects positive case."""
        num_records = 150
        ShipDataHistoryFactory.create_batch(size=num_records)

        with self.assertLogs() as captured:
            call_command(
                'flaghistory',
                'populate',
            )

            assert captured.output == [
                f'INFO:management:Populating flag history...',
                f'INFO:management:100/{num_records} done',
                f'INFO:management:{num_records}/{num_records} done',
                f'INFO:management:{num_records} flag history records created successfully.',
                'WARNING:management:0 flag history records marked as ignored.',
            ]

        assert num_records == FlagHistory.objects.count()

    def test_populate_flag_history_with_incorrect_flag_effective_date(self):
        """Test populate flag history with incorrect effective dates positive case."""
        data = [
            {
                'imo_id': '1234567',
                'flag_name': 'Brazil',
                'flag_effective_date': '201910',
                'timestamp': datetime(2019, 3, 9, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Tanzania',
                'flag_effective_date': '201909',
                'timestamp': datetime(2019, 9, 9, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Brazil',
                'flag_effective_date': '202002',
                'timestamp': datetime(2020, 2, 14, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Unknown',
                'flag_effective_date': '202108',
                'timestamp': datetime(2020, 8, 17, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Malta',
                'flag_effective_date': '202104',
                'timestamp': datetime(2021, 4, 2, tzinfo=pytz.UTC),
            },
        ]
        override_data = [
            {
                'ignore': True,
                'flag_effective_date': datetime(2019, 10, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': False,
                'flag_effective_date': datetime(2019, 9, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': False,
                'flag_effective_date': datetime(2020, 2, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': True,
                'flag_effective_date': datetime(2021, 8, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': False,
                'flag_effective_date': datetime(2021, 4, 1, tzinfo=pytz.UTC),
            },
        ]
        num_records = len(data)

        for ship, override_ship in zip(data, override_data):
            ShipDataHistoryFactory.create(**ship)
            ship.update(override_ship)

        with self.assertLogs() as captured:
            call_command(
                'flaghistory',
                'populate',
            )

            assert captured.output == [
                'INFO:management:Populating flag history...',
                f'INFO:management:{num_records}/{num_records} done',
                f'INFO:management:{num_records} flag history records created successfully.',
                'WARNING:management:2 flag history records marked as ignored.',
            ]

        results = FlagHistory.objects.order_by('timestamp')
        for expected, flag in zip(data, results):
            for key, value in expected.items():
                assert value == getattr(flag, key)

    def test_populate_flag_history_with_duplicated_flag_names(self):
        """Test populate flag history with duplicated flag names positive case."""
        data = [
            {
                'imo_id': '1234567',
                'flag_name': 'Liberia',
                'flag_effective_date': '201803',
                'timestamp': datetime(2018, 3, 9, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Liberia',
                'flag_effective_date': '201807',
                'timestamp': datetime(2018, 7, 21, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Zimbabwe',
                'flag_effective_date': '201903',
                'timestamp': datetime(2019, 3, 3, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Liberia',
                'flag_effective_date': '201910',
                'timestamp': datetime(2019, 10, 2, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Liberia',
                'flag_effective_date': '202001',
                'timestamp': datetime(2020, 1, 10, tzinfo=pytz.UTC),
            },
        ]
        override_data = [
            {
                'ignore': True,
                'flag_effective_date': datetime(2018, 3, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': False,
                'flag_effective_date': datetime(2018, 7, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': False,
                'flag_effective_date': datetime(2019, 3, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': True,
                'flag_effective_date': datetime(2019, 10, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': False,
                'flag_effective_date': datetime(2020, 1, 1, tzinfo=pytz.UTC),
            },
        ]
        num_records = len(data)

        for ship, override_ship in zip(data, override_data):
            ShipDataHistoryFactory.create(**ship)
            ship.update(override_ship)

        with self.assertLogs() as captured:
            call_command(
                'flaghistory',
                'populate',
            )

            assert captured.output == [
                'INFO:management:Populating flag history...',
                f'INFO:management:{num_records}/{num_records} done',
                f'INFO:management:{num_records} flag history records created successfully.',
                'WARNING:management:2 flag history records marked as ignored.',
            ]

        results = FlagHistory.objects.order_by('timestamp')
        for expected, flag in zip(data, results):
            for key, value in expected.items():
                assert value == getattr(flag, key)

    def test_populate_flag_history_another_test(self):
        """Test populate flag history with duplicated flag names positive case."""
        data = [
            {
                'imo_id': '1234567',
                'flag_name': 'Panama',
                'flag_effective_date': '202011',
                'timestamp': datetime(2020, 11, 18, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Korea, South',
                'flag_effective_date': '202009',
                'timestamp': datetime(2020, 9, 18, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Marshall Islands ',
                'flag_effective_date': '202009',
                'timestamp': datetime(2020, 8, 13, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Marshall Islands ',
                'flag_effective_date': '202008',
                'timestamp': datetime(2020, 4, 16, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Marshall Islands ',
                'flag_effective_date': '202007',
                'timestamp': datetime(2018, 5, 19, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Panama',
                'flag_effective_date': '202007',
                'timestamp': datetime(2017, 11, 9, tzinfo=pytz.UTC),
            },
        ]

        override_data = [
            {
                'ignore': False,
                'flag_effective_date': datetime(2020, 11, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': False,
                'flag_effective_date': datetime(2020, 9, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': True,
                'flag_effective_date': datetime(2020, 9, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': True,
                'flag_effective_date': datetime(2020, 8, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': True,
                'flag_effective_date': datetime(2020, 7, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': True,
                'flag_effective_date': datetime(2020, 7, 1, tzinfo=pytz.UTC),
            },
        ]

        num_records = len(data)

        for ship, override_ship in zip(data, override_data):
            ShipDataHistoryFactory.create(**ship)
            ship.update(override_ship)

        with self.assertLogs() as captured:
            call_command(
                'flaghistory',
                'populate',
            )

            assert captured.output == [
                'INFO:management:Populating flag history...',
                f'INFO:management:{num_records}/{num_records} done',
                f'INFO:management:{num_records} flag history records created successfully.',
                'WARNING:management:4 flag history records marked as ignored.',
            ]

        results = FlagHistory.objects.order_by('-timestamp')
        for expected, flag in zip(data, results):
            for key, value in expected.items():
                assert value == getattr(flag, key)

    def test_populate_flag_history_with_duplicated_effective_dates(self):
        """Test populate flag history with duplicated effective dates positive case."""
        data = [
            {
                'imo_id': '1234567',
                'flag_name': 'Zimbabwe',
                'flag_effective_date': '202001',
                'timestamp': datetime(2020, 1, 12, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Liberia',
                'flag_effective_date': '202001',
                'timestamp': datetime(2020, 1, 13, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Denmark',
                'flag_effective_date': '202112',
                'timestamp': datetime(2021, 12, 3, tzinfo=pytz.UTC),
            },
            {
                'imo_id': '1234567',
                'flag_name': 'Unknown',
                'flag_effective_date': '202112',
                'timestamp': datetime(2021, 12, 27, tzinfo=pytz.UTC),
            },
        ]
        override_data = [
            {
                'ignore': True,
                'flag_effective_date': datetime(2020, 1, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': False,
                'flag_effective_date': datetime(2020, 1, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': True,
                'flag_effective_date': datetime(2021, 12, 1, tzinfo=pytz.UTC),
            },
            {
                'ignore': False,
                'flag_effective_date': datetime(2021, 12, 1, tzinfo=pytz.UTC),
            },
        ]
        num_records = len(data)

        for ship, override_ship in zip(data, override_data):
            ShipDataHistoryFactory.create(**ship)
            ship.update(override_ship)

        with self.assertLogs() as captured:
            call_command(
                'flaghistory',
                'populate',
            )

            assert captured.output == [
                'INFO:management:Populating flag history...',
                f'INFO:management:{num_records}/{num_records} done',
                f'INFO:management:{num_records} flag history records created successfully.',
                'WARNING:management:2 flag history records marked as ignored.',
            ]

        results = FlagHistory.objects.order_by('timestamp')
        for expected, flag in zip(data, results):
            for key, value in expected.items():
                assert value == getattr(flag, key)

    def test_populate_flag_history_with_invalid_effective_date_month(self):
        """Test populate flag history with invalid month value in flag effective date positive case."""
        data = [
            {
                'imo_id': '1234567',
                'flag_name': 'Australia',
                'flag_effective_date': '202299',
            },
        ]
        override_data = [
            {
                'ignore': False,
                'flag_effective_date': datetime(2022, 1, 1, tzinfo=pytz.UTC),
            },
        ]
        num_records = len(data)

        for ship, override_ship in zip(data, override_data):
            ShipDataHistoryFactory.create(**ship, year_of_build=2010)
            ship.update(override_ship)

        with self.assertLogs() as captured:
            call_command(
                'flaghistory',
                'populate',
            )

            assert captured.output == [
                'INFO:management:Populating flag history...',
                f'INFO:management:{num_records}/{num_records} done',
                f'INFO:management:{num_records} flag history records created successfully.',
                'WARNING:management:0 flag history records marked as ignored.',
            ]

        results = FlagHistory.objects.order_by('timestamp')
        for expected, flag in zip(data, results):
            for key, value in expected.items():
                assert value == getattr(flag, key)

    def test_populate_flag_history_with_invalid_effective_date(self):
        """Test populate flag history with invalid flag effective date positive case."""
        data = [
            {
                'imo_id': '1234567',
                'flag_name': 'Australia',
                'flag_effective_date': 'invalid',
                'timestamp': datetime(1994, 8, 24, tzinfo=pytz.UTC),
            },
        ]
        override_data = [
            {
                'ignore': False,
                'flag_effective_date': datetime(1994, 8, 24, tzinfo=pytz.UTC),
            },
        ]
        num_records = len(data)

        for ship, override_ship in zip(data, override_data):
            ShipDataHistoryFactory.create(**ship, year_of_build=1975)
            ship.update(override_ship)

        with self.assertLogs() as captured:
            call_command(
                'flaghistory',
                'populate',
            )

            assert captured.output == [
                'INFO:management:Populating flag history...',
                f'INFO:management:{num_records}/{num_records} done',
                f'INFO:management:{num_records} flag history records created successfully.',
                'WARNING:management:0 flag history records marked as ignored.',
            ]

        results = FlagHistory.objects.order_by('timestamp')
        for expected, flag in zip(data, results):
            for key, value in expected.items():
                assert value == getattr(flag, key)

    def test_ignore_flag_history(self):
        """Test ignore flag history positive case."""
        data = [
            {'manual_edit': False, 'ignore': True},
            {'manual_edit': True, 'ignore': False},
            {'manual_edit': False, 'ignore': True},
        ]
        expected_outputs = [True, True, False]

        for flag in data:
            FlagHistoryFactory(imo_id=12345678, flag_name='Denmark', **flag)

        call_command('flaghistory', 'ignore')

        results = FlagHistory.objects.order_by('timestamp').values_list(
            'ignore', flat=True
        )
        for expected, result in zip(expected_outputs, results):
            assert expected is result

    def test_ignore_flag_history_with_manual_records_excluded(self):
        """Test ignore flag history with manual records excluded positive case."""
        data = [
            {'manual_edit': False, 'ignore': True},
            {'manual_edit': True, 'ignore': False},
            {'manual_edit': False, 'ignore': True},
        ]
        expected_outputs = [True, False, False]

        for flag in data:
            FlagHistoryFactory(imo_id=12345678, flag_name='Denmark', **flag)

        call_command('flaghistory', 'ignore', '--exclude-manual')

        results = FlagHistory.objects.order_by('timestamp').values_list(
            'ignore', flat=True
        )
        for expected, result in zip(expected_outputs, results):
            assert expected is result

    def test_populate_company_history(self):
        """Test populate company history positive case."""
        num_records = 10
        ShipDataHistoryFactory.create_batch(size=num_records)

        with self.assertLogs() as captured:
            call_command('companyhistory', 'populate')
            assert captured.output == [
                f'INFO:management:Populating company history...',
                f'INFO:management:{num_records}/{num_records} IMOs done',
                f'INFO:management:{num_records * len(CompanyAssociationTypes)} company history records created successfully.',
                'WARNING:management:0 company history records marked as ignored.',
            ]

        assert (
            num_records * len(CompanyAssociationTypes) == CompanyHistory.objects.count()
        )

    def test_populate_company_history_with_duplicated_ship_data(self):
        """Test populate company history with duplicated ship data positive case."""
        num_records = 5

        ShipDataHistoryFactory.create_batch(
            size=num_records,
            imo_id='1234567',
            operator='Foo Inc.',
            operator_code=123,
            operator_registration_country='Panama',
            operator_control_country='Australia',
            operator_domicile_country='Malta',
        )
        ShipDataHistoryFactory.create_batch(
            size=num_records,
            imo_id='1234567',
            operator='Bar Ltd.',
            operator_code=321,
            operator_registration_country='Zimbabwe',
            operator_control_country='Liberia',
            operator_domicile_country='Marshall Islands',
        )
        ShipDataHistoryFactory.create_batch(
            size=num_records,
            imo_id='1234567',
            operator='Foo Inc.',
            operator_code=123,
            operator_registration_country='Panama',
            operator_control_country='Australia',
            operator_domicile_country='Malta',
        )

        call_command('companyhistory', 'populate')

        # 1 historical record for intermediate company
        assert CompanyHistory.objects.filter(company_code=321).count() == 1
        # 2 historical records for company that was changed and then came back on the list
        # we should track such changes to avoid loss of company hopping
        assert CompanyHistory.objects.filter(company_code=123).count() == 2
        # all historical records for company with unique values
        assert (
            CompanyHistory.objects.filter(
                association_type=CompanyAssociationTypes.SHIP_MANAGER.value
            ).count()
            == num_records * 3
        )

    def test_populate_company_history_with_empty_ship_data(self):
        """Test populate company history with no ship data positive case."""
        with self.assertLogs() as captured:
            call_command('companyhistory', 'populate')

            assert captured.output == [
                'INFO:management:Populating company history...',
                'ERROR:management:No company history records created.',
            ]

        assert CompanyHistory.objects.count() == 0

    def test_populate_company_history_with_full_batch(self):
        """Test populate company history with full batch of ship history objects positive case."""
        num_records = 150
        ShipDataHistoryFactory.create_batch(size=num_records)

        with self.assertLogs() as captured:
            call_command('companyhistory', 'populate')

            assert captured.output == [
                'INFO:management:Populating company history...',
                f'INFO:management:100/{num_records} IMOs done',
                f'INFO:management:{num_records}/{num_records} IMOs done',
                f'INFO:management:{num_records * len(CompanyAssociationTypes)} company history records created successfully.',
                'WARNING:management:0 company history records marked as ignored.',
            ]

        assert (
            num_records * len(CompanyAssociationTypes) == CompanyHistory.objects.count()
        )

    def test_populate_company_history_with_duplicated_records(self):
        """Test populate company history with records that have same imo_id and company_code positive case."""
        num_records = 5
        num_ignored = (num_records - 1) * 3
        num_total_records = num_records * len(CompanyAssociationTypes) * 3

        ships1 = ShipDataHistoryFactory.create_batch(
            size=num_records,
            imo_id='1234567',
            registered_owner_code=999,
        )
        expected_ships1_timestamp = get_last(ships1).timestamp

        ships2 = ShipDataHistoryFactory.create_batch(
            size=num_records,
            imo_id='1234567',
            registered_owner_code=321,
        )
        expected_ships2_timestamp = get_last(ships2).timestamp

        ships3 = ShipDataHistoryFactory.create_batch(
            size=num_records,
            imo_id='1234567',
            registered_owner_code=999,
        )
        expected_ships3_timestamp = get_last(ships3).timestamp

        with self.assertLogs() as captured:
            call_command('companyhistory', 'populate')

            assert captured.output == [
                'INFO:management:Populating company history...',
                f'INFO:management:1/1 IMOs done',
                f'INFO:management:{num_total_records} company history records created successfully.',
                f'WARNING:management:{num_ignored} company history records marked as ignored.',
            ]

        assert CompanyHistory.objects.count() == num_total_records
        assert CompanyHistory.objects.filter(ignore=True).count() == num_ignored
        assert (
            CompanyHistory.objects.filter(
                association_type=CompanyAssociationTypes.REGISTERED_OWNER.value,
                ignore=False,
            ).count()
            == 3
        )
        assert list(
            CompanyHistory.objects.filter(
                association_type=CompanyAssociationTypes.REGISTERED_OWNER.value,
                ignore=False,
            )
            .values_list('timestamp', flat=True)
            .order_by('timestamp')
        ) == [
            expected_ships1_timestamp,
            expected_ships2_timestamp,
            expected_ships3_timestamp,
        ]

    def test_populate_company_history_effective_date_without_preceding_history(self):
        """Test populate company history effective_date field for new history positive case."""
        batch1 = ShipDataHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            operator_code=73312,
        )
        expected_batch1_effective_date = get_first(batch1).timestamp

        batch2 = ShipDataHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            operator_code=23421,
        )
        expected_batch2_effective_date = get_first(batch2).timestamp

        batch3 = ShipDataHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            operator_code=73312,
        )
        expected_batch3_effective_date = get_first(batch3).timestamp

        call_command('companyhistory', 'populate')

        for expected_effective_date in [
            expected_batch1_effective_date,
            expected_batch2_effective_date,
            expected_batch3_effective_date,
        ]:
            assert (
                CompanyHistory.objects.filter(
                    association_type=CompanyAssociationTypes.OPERATOR.value,
                    effective_date=expected_effective_date,
                ).count()
                == 5
            )

    def test_populate_company_history_effective_date_with_preceding_company(self):
        """Test populate company history effective_date field for preceding history positive case."""
        batch1 = ShipDataHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            operator_code=52333,
        )
        expected_batch1_effective_date = get_first(batch1).timestamp

        batch2 = ShipDataHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            operator_code=73312,
        )
        expected_batch2_effective_date = get_first(batch2).timestamp

        call_command('companyhistory', 'populate')

        for expected_effective_date in [
            expected_batch1_effective_date,
            expected_batch2_effective_date,
        ]:
            assert (
                CompanyHistory.objects.filter(
                    association_type=CompanyAssociationTypes.OPERATOR.value,
                    effective_date=expected_effective_date,
                ).count()
                == 5
            )

    def test_populate_company_history_with_blank_company(self):
        """Test populate company history with blank company_name positive case."""
        ShipDataHistoryFactory.create(
            imo_id=12345678,
            operator='',
            operator_code=12345678,
        )

        call_command('companyhistory', 'populate')

        company = CompanyHistory.objects.get(
            association_type=CompanyAssociationTypes.OPERATOR.value
        )
        assert company.company_name == UNKNOWN_COMPANY_NAME
        assert company.company_code == UNKNOWN_COMPANY_CODE

    def test_ignore_company_history(self):
        """Test ignore company history positive case."""
        data = [
            {'manual_edit': False, 'ignore': True},
            {'manual_edit': True, 'ignore': False},
            {'manual_edit': False, 'ignore': True},
        ]
        expected_outputs = [True, True, False]

        for company in data:
            CompanyHistoryFactory(
                imo_id=12345678,
                company_code=123,
                association_type=CompanyAssociationTypes.TECHNICAL_MANAGER.value,
                **company,
            )

        call_command('companyhistory', 'ignore')

        results = CompanyHistory.objects.order_by('timestamp').values_list(
            'ignore', flat=True
        )
        for expected, result in zip(expected_outputs, results):
            assert expected is result

    def test_ignore_company_history_with_manual_records_excluded(self):
        """Test ignore company history with manual records excluded positive case."""
        data = [
            {'manual_edit': False, 'ignore': True},
            {'manual_edit': True, 'ignore': False},
            {'manual_edit': False, 'ignore': True},
        ]
        expected_outputs = [True, False, False]

        for company in data:
            CompanyHistoryFactory(
                imo_id=12345678,
                company_code=123,
                association_type=CompanyAssociationTypes.TECHNICAL_MANAGER.value,
                **company,
            )

        # TODO: substitute exclude_manual argument as options parameter
        #  after migrating to Django 3 (https://code.djangoproject.com/ticket/30584)
        call_command('companyhistory', 'ignore', '--exclude-manual')

        results = CompanyHistory.objects.order_by('timestamp').values_list(
            'ignore', flat=True
        )
        for expected, result in zip(expected_outputs, results):
            assert expected is result
