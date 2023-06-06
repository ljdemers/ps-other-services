from datetime import datetime
import json
from socket import timeout

from freezegun import freeze_time
import pytest
import responses

from screening_api.screenings.enums import Severity, Status

from screening_workers.lib.utils import date2str, DATE_FORMAT
from screening_workers.screenings_profiles.models import (
    DefaultScreeningProfile as ScreeningProfile,
)
from screening_workers.ship_inspections.checks import ShipInspectionsCheck
from screening_workers.ship_inspections.tasks import ShipInspectionsCheckTask


class TestShipInspectionsTask:

    @pytest.fixture
    def check(self, application):
        return ShipInspectionsCheck(
            application.screenings_repository,
            application.screenings_reports_repository,
            application.ship_inspections_repository,
            application.ship_inspections_updater,
        )

    @pytest.fixture
    def task(self, application):
        return application.tasks[ShipInspectionsCheckTask.name]

    def test_registered(self, application):
        assert ShipInspectionsCheckTask.name in application.tasks

    def test_screening_not_found(self, application, factory, task):
        screening_id = 1234567
        task_args = (screening_id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening_id)
        assert screening is None

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening_id)
        assert report is None

    @pytest.mark.usefixtures('mock_task_run')
    def test_timeout(
            self, mock_task_run, application, factory, task, sis_client):
        mock_task_run.side_effect = timeout
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(
            ship=ship, account_id=account_id,
            severity=Severity.UNKNOWN, status=Status.SCHEDULED,
        )

        task_args = (screening.id, )

        result = task.apply(task_args)

        with pytest.raises(timeout):
            result.get()

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity == Severity.UNKNOWN
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is None

    @responses.activate
    def test_no_inspections(self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier',
            length=123.4, breadth=234.5, displacement=345.6, draught=456.7,
        )
        screening = factory.create_screening(
            ship=ship, account_id=account_id,
            severity=Severity.UNKNOWN, status=Status.SCHEDULED,
        )

        response = {
            'objects': [],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity == Severity.OK
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [],
        }

    @responses.activate
    def test_no_inspections_no_update(
            self, application, factory, task, ship_inspections_update_cache):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        ship_inspections_update_cache.put(str(ship.id), datetime.utcnow())
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity == Severity.OK
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [],
        }

    @responses.activate
    def test_no_inspections_update_not_detained_no_defects(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)

        response = {
            'objects': [
                {
                    'authorisation': "US Coastguard",
                    'detained': False,
                    'inspection_id': "123456789012345",
                    'inspection_date': "2009-01-28",
                    'number_part_days_detained': None,
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity == Severity.OK
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': False,
                    'detained_days': 0.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2009-01-28',
                    'port_name': 'San Juan, Puerto Rico',
                },
            ],
        }

    @responses.activate
    @freeze_time("2017-09-11 07:59:00")
    def test_no_inspections_update_detained(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)

        response = {
            'objects': [
                {
                    'authorisation': "US Coastguard",
                    'detained': True,
                    'inspection_id': "123456789012345",
                    'inspection_date': "2009-01-28",
                    'number_part_days_detained': '1.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity == Severity.OK
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': True,
                    'detained_days': 1.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2009-01-28',
                    'port_name': 'San Juan, Puerto Rico',
                },
            ],
        }

    @responses.activate
    def test_no_inspections_update_defects(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)

        response = {
            'objects': [
                {
                    'authorisation': "US Coastguard",
                    'detained': False,
                    'inspection_id': "123456789012345",
                    'inspection_date': "2009-01-28",
                    'number_part_days_detained': '0.0',
                    'no_defects': 2,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity ==\
            ScreeningProfile.ship_deficiency_severity
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 2,
                    'defects_count_severity': 'OK',
                    'detained': False,
                    'detained_days': 0.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2009-01-28',
                    'port_name': 'San Juan, Puerto Rico',
                },
            ],
        }

    @responses.activate
    def test_no_inspections_update_1_detained_over_24_months_ago(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)

        response = {
            'objects': [
                {
                    'authorisation': "US Coastguard",
                    'detained': True,
                    'inspection_id': "123456789012345",
                    'inspection_date': "2001-09-11",
                    'number_part_days_detained': '1.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
                {
                    'authorisation': "US Coastguard",
                    'detained': False,
                    'inspection_id': "123456789012346",
                    'inspection_date': "2001-09-12",
                    'number_part_days_detained': None,
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity ==\
            ScreeningProfile.ship_detained_in_over_24_months_severity
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': False,
                    'detained_days': 0.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2001-09-12',
                    'port_name': 'San Juan, Puerto Rico',
                },
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': True,
                    'detained_days': 1.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2001-09-11',
                    'port_name': 'San Juan, Puerto Rico',
                },
            ],
        }

    @responses.activate
    @freeze_time("2017-09-11 07:59:00")
    def test_no_inspections_update_1_detained_in_24_months(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)

        response = {
            'objects': [
                {
                    'authorisation': "US Coastguard",
                    'detained': True,
                    'inspection_id': "123456789012345",
                    'inspection_date': "2015-12-30",
                    'number_part_days_detained': '1.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
                {
                    'authorisation': "US Coastguard",
                    'detained': False,
                    'inspection_id': "123456789012346",
                    'inspection_date': "2016-09-12",
                    'number_part_days_detained': None,
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity == Severity.OK
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': False,
                    'detained_days': 0.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2016-09-12',
                    'port_name': 'San Juan, Puerto Rico',
                },
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': True,
                    'detained_days': 1.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2015-12-30',
                    'port_name': 'San Juan, Puerto Rico',
                },
            ],
        }

    @responses.activate
    @freeze_time("2017-09-11 07:59:00")
    def test_no_inspections_update_2_detained_in_24_months(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)

        response = {
            'objects': [
                {
                    'authorisation': "US Coastguard",
                    'detained': True,
                    'inspection_id': "123456789012344",
                    'inspection_date': "2015-12-30",
                    'number_part_days_detained': '1.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
                {
                    'authorisation': "US Coastguard",
                    'detained': True,
                    'inspection_id': "123456789012345",
                    'inspection_date': "2016-03-11",
                    'number_part_days_detained': '1.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
                {
                    'authorisation': "US Coastguard",
                    'detained': False,
                    'inspection_id': "123456789012346",
                    'inspection_date': "2016-09-12",
                    'number_part_days_detained': None,
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity ==\
            ScreeningProfile.ship_2_or_more_detained_in_24_months_severity
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': False,
                    'detained_days': 0.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2016-09-12',
                    'port_name': 'San Juan, Puerto Rico',
                },
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': True,
                    'detained_days': 1.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2016-03-11',
                    'port_name': 'San Juan, Puerto Rico',
                },
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': True,
                    'detained_days': 1.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2015-12-30',
                    'port_name': 'San Juan, Puerto Rico',
                },
            ],
        }

    @responses.activate
    @freeze_time("2017-09-11 07:59:00")
    def test_no_inspections_update_1_detained_in_12_months(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)

        response = {
            'objects': [
                {
                    'authorisation': "Tokyo MOU",
                    'detained': True,
                    'inspection_id': "123456789012344",
                    'inspection_date': "2016-03-30",
                    'number_part_days_detained': '1.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
                {
                    'authorisation': "Tokyo MOU",
                    'detained': True,
                    'inspection_id': "123456789012345",
                    'inspection_date': "2017-06-30",
                    'number_part_days_detained': '1.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
                {
                    'authorisation': "US Coastguard",
                    'detained': False,
                    'inspection_id': "123456789012346",
                    'inspection_date': "2017-07-30",
                    'number_part_days_detained': None,
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity ==\
            ScreeningProfile.ship_1_or_more_detained_in_12_months_severity
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': False,
                    'detained_days': 0.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2017-07-30',
                    'port_name': 'San Juan, Puerto Rico',
                },
                {
                    'authority': 'Tokyo MOU',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': True,
                    'detained_days': 1.0,
                    'detained_days_severity': 'WARNING',
                    'inspection_date': '2017-06-30',
                    'port_name': 'San Juan, Puerto Rico',
                },
                {
                    'authority': 'Tokyo MOU',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': True,
                    'detained_days': 1.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2016-03-30',
                    'port_name': 'San Juan, Puerto Rico',
                },
            ],
        }

    @responses.activate
    @pytest.mark.parametrize(
        'authority', ShipInspectionsCheck.CRITICAL_AUTHORITIES)
    @freeze_time("2017-09-11 07:59:00")
    def test_no_inspections_update_1_detained_in_12_months_ca(
            self, application, factory, task, sis_client, authority):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)

        response = {
            'objects': [
                {
                    'authorisation': "US Coastguard",
                    'detained': True,
                    'inspection_id': "123456789012344",
                    'inspection_date': "2016-03-30",
                    'number_part_days_detained': '1.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
                {
                    'authorisation': authority,
                    'detained': True,
                    'inspection_id': "123456789012345",
                    'inspection_date': "2017-06-30",
                    'number_part_days_detained': '1.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
                {
                    'authorisation': "US Coastguard",
                    'detained': False,
                    'inspection_id': "123456789012346",
                    'inspection_date': "2017-07-30",
                    'number_part_days_detained': None,
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity ==\
            ScreeningProfile.ship_1_or_more_detained_in_12_months_ca_severity
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': False,
                    'detained_days': 0.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2017-07-30',
                    'port_name': 'San Juan, Puerto Rico',
                },
                {
                    'authority': authority,
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': True,
                    'detained_days': 1.0,
                    'detained_days_severity': 'CRITICAL',
                    'inspection_date': '2017-06-30',
                    'port_name': 'San Juan, Puerto Rico',
                },
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': True,
                    'detained_days': 1.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2016-03-30',
                    'port_name': 'San Juan, Puerto Rico',
                },
            ],
        }

    @responses.activate
    @freeze_time("2017-09-11 07:59:00")
    def test_no_inspections_update_2_detained_in_12_months(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)

        response = {
            'objects': [
                {
                    'authorisation': "Tokyo MOU",
                    'detained': True,
                    'inspection_id': "123456789012344",
                    'inspection_date': "2017-03-30",
                    'number_part_days_detained': '1.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
                {
                    'authorisation': "Tokyo MOU",
                    'detained': True,
                    'inspection_id': "123456789012345",
                    'inspection_date': "2017-06-30",
                    'number_part_days_detained': '1.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
                {
                    'authorisation': "US Coastguard",
                    'detained': False,
                    'inspection_id': "123456789012346",
                    'inspection_date': "2017-07-30",
                    'number_part_days_detained': None,
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity ==\
            ScreeningProfile.ship_2_or_more_detained_in_12_months_severity
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': False,
                    'detained_days': 0.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2017-07-30',
                    'port_name': 'San Juan, Puerto Rico',
                },
                {
                    'authority': 'Tokyo MOU',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': True,
                    'detained_days': 1.0,
                    'detained_days_severity': 'CRITICAL',
                    'inspection_date': '2017-06-30',
                    'port_name': 'San Juan, Puerto Rico',
                },
                {
                    'authority': 'Tokyo MOU',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': True,
                    'detained_days': 1.0,
                    'detained_days_severity': 'WARNING',
                    'inspection_date': '2017-03-30',
                    'port_name': 'San Juan, Puerto Rico',
                },
            ],
        }

    @responses.activate
    def test_inspection_not_detained_no_defects(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        inspection = factory.create_ship_inspection(
            ship=ship, detained_days=0.0, defects_count=0)

        response = {
            'objects': [],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity == Severity.OK
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': inspection.authority,
                    'country_name': inspection.country_name,
                    'defects_count': inspection.defects_count,
                    'defects_count_severity': 'OK',
                    'detained': inspection.detained,
                    'detained_days': inspection.detained_days,
                    'detained_days_severity': 'OK',
                    'inspection_date': date2str(
                        inspection.inspection_date, date_format=DATE_FORMAT),
                    'port_name': inspection.port_name,
                },
            ],
        }

    @responses.activate
    def test_inspection_defects(self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        inspection = factory.create_ship_inspection(
            ship=ship, detained_days=0.0, defects_count=1)

        response = {
            'objects': [],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity ==\
            ScreeningProfile.ship_deficiency_severity
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': inspection.authority,
                    'country_name': inspection.country_name,
                    'defects_count': inspection.defects_count,
                    'defects_count_severity': 'OK',
                    'detained': inspection.detained,
                    'detained_days': inspection.detained_days,
                    'detained_days_severity': 'OK',
                    'inspection_date': date2str(
                        inspection.inspection_date, date_format=DATE_FORMAT),
                    'port_name': inspection.port_name,
                },
            ],
        }

    @responses.activate
    def test_inspection_not_detained_update_detained(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        inspection = factory.create_ship_inspection(
            ship=ship, detained_days=0.0, defects_count=0)

        response = {
            'objects': [
                {
                    'authorisation': "US Coastguard",
                    'detained': True,
                    'inspection_id': "123456789012345",
                    'inspection_date': "2109-01-28",
                    'number_part_days_detained': '1.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity ==\
            ScreeningProfile.ship_last_inspection_detained_severity
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': "US Coastguard",
                    'country_name': "USA",
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': True,
                    'detained_days': 1.0,
                    'detained_days_severity': 'CRITICAL',
                    'inspection_date': "2109-01-28",
                    'port_name': "San Juan, Puerto Rico",
                },
                {
                    'authority': inspection.authority,
                    'country_name': inspection.country_name,
                    'defects_count': inspection.defects_count,
                    'defects_count_severity': 'OK',
                    'detained': inspection.detained,
                    'detained_days': inspection.detained_days,
                    'detained_days_severity': 'OK',
                    'inspection_date': date2str(
                        inspection.inspection_date, date_format=DATE_FORMAT),
                    'port_name': inspection.port_name,
                },
            ],
        }

    @responses.activate
    def test_inspection_defects_update_no_defects(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        inspection = factory.create_ship_inspection(
            ship=ship, detained_days=0.0, defects_count=1)

        response = {
            'objects': [
                {
                    'authorisation': "US Coastguard",
                    'detained': False,
                    'inspection_id': "123456789012345",
                    'inspection_date': "2109-01-28",
                    'number_part_days_detained': '0.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity ==\
            ScreeningProfile.ship_deficiency_severity
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': "US Coastguard",
                    'country_name': "USA",
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': False,
                    'detained_days': 0.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': "2109-01-28",
                    'port_name': "San Juan, Puerto Rico",
                },
                {
                    'authority': inspection.authority,
                    'country_name': inspection.country_name,
                    'defects_count': inspection.defects_count,
                    'defects_count_severity': 'OK',
                    'detained': inspection.detained,
                    'detained_days': inspection.detained_days,
                    'detained_days_severity': 'OK',
                    'inspection_date': date2str(
                        inspection.inspection_date, date_format=DATE_FORMAT),
                    'port_name': inspection.port_name,
                },
            ],
        }

    @responses.activate
    def test_inspection_not_detained_duplicate_update(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        inspection = factory.create_ship_inspection(
            ship=ship, detained_days=0.0, defects_count=0,
            inspection_id="123456789012345",
        )

        response = {
            'objects': [
                {
                    'authorisation': "US Coastguard",
                    'detained': True,
                    'inspection_id': "123456789012345",
                    'inspection_date': "2009-01-28",
                    'number_part_days_detained': '1.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity == Severity.OK
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': inspection.authority,
                    'country_name': inspection.country_name,
                    'defects_count': inspection.defects_count,
                    'defects_count_severity': 'OK',
                    'detained': inspection.detained,
                    'detained_days': inspection.detained_days,
                    'detained_days_severity': 'OK',
                    'inspection_date': date2str(
                        inspection.inspection_date, date_format=DATE_FORMAT),
                    'port_name': inspection.port_name,
                },
            ],
        }

    @responses.activate
    @freeze_time("2017-09-11 07:59:00")
    def test_last_inspection_detained(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        inspection = factory.create_ship_inspection(
            ship=ship, detained=True, detained_days=1.0, defects_count=0)

        response = {
            'objects': [],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity ==\
            ScreeningProfile.ship_last_inspection_detained_severity
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': inspection.authority,
                    'country_name': inspection.country_name,
                    'defects_count': inspection.defects_count,
                    'defects_count_severity': 'OK',
                    'detained': inspection.detained,
                    'detained_days': inspection.detained_days,
                    'detained_days_severity': 'CRITICAL',
                    'inspection_date': date2str(
                        inspection.inspection_date, date_format=DATE_FORMAT),
                    'port_name': inspection.port_name,
                },
            ],
        }

    @responses.activate
    @freeze_time("2017-09-11 07:59:00")
    def test_last_inspection_detained_more_than_year(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        inspection = factory.create_ship_inspection(
            ship=ship, detained=True, detained_days=1.0, defects_count=0,
            inspection_date="2016-09-01 07:59:00",
        )

        response = {
            'objects': [],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity ==\
            ScreeningProfile.ship_once_detained_in_24_months_severity
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': inspection.authority,
                    'country_name': inspection.country_name,
                    'defects_count': inspection.defects_count,
                    'defects_count_severity': 'OK',
                    'detained': inspection.detained,
                    'detained_days': inspection.detained_days,
                    'detained_days_severity': 'OK',
                    'inspection_date': date2str(
                        inspection.inspection_date, date_format=DATE_FORMAT),
                    'port_name': inspection.port_name,
                },
            ],
        }

    @responses.activate
    def test_last_inspection_detained_less_than_day(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        inspection = factory.create_ship_inspection(
            ship=ship, detained=True, detained_days=0.0, defects_count=0)

        response = {
            'objects': [],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity ==\
            ScreeningProfile.ship_last_inspection_detained_severity
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': inspection.authority,
                    'country_name': inspection.country_name,
                    'defects_count': inspection.defects_count,
                    'defects_count_severity': 'OK',
                    'detained': inspection.detained,
                    'detained_days': inspection.detained_days,
                    'detained_days_severity': 'CRITICAL',
                    'inspection_date': date2str(
                        inspection.inspection_date, date_format=DATE_FORMAT),
                    'port_name': inspection.port_name,
                },
            ],
        }

    @freeze_time("2017-09-11 07:59:00")
    @responses.activate
    def test_existing_detained_inspections(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        inspection1 = factory.create_ship_inspection(
            ship=ship, inspection_date='2001-09-11',
            detained_days=1.0, defects_count=0,
        )
        inspection2 = factory.create_ship_inspection(
            ship=ship, inspection_date='2001-09-12',
            detained_days=0.0, defects_count=0,
        )

        response = {
            'objects': [],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity ==\
            ScreeningProfile.ship_detained_in_over_24_months_severity
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': inspection2.authority,
                    'country_name': inspection2.country_name,
                    'defects_count': inspection2.defects_count,
                    'defects_count_severity': 'OK',
                    'detained': inspection2.detained,
                    'detained_days': inspection2.detained_days,
                    'detained_days_severity': 'OK',
                    'inspection_date': date2str(
                        inspection2.inspection_date, date_format=DATE_FORMAT),
                    'port_name': inspection2.port_name,
                },
                {
                    'authority': inspection1.authority,
                    'country_name': inspection1.country_name,
                    'defects_count': inspection1.defects_count,
                    'defects_count_severity': 'OK',
                    'detained': inspection1.detained,
                    'detained_days': inspection1.detained_days,
                    'detained_days_severity': 'OK',
                    'inspection_date': date2str(
                        inspection1.inspection_date, date_format=DATE_FORMAT),
                    'port_name': inspection1.port_name,
                },
            ],
        }

    @responses.activate
    @freeze_time("2017-09-11 07:59:00")
    def test_existing_detained_inspections_update_detained(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        inspection1 = factory.create_ship_inspection(
            ship=ship, inspection_date='2001-09-11',
            detained_days=1.0, defects_count=0,
        )
        inspection2 = factory.create_ship_inspection(
            ship=ship, inspection_date='2001-09-12',
            detained_days=0.0, defects_count=0,
        )

        response = {
            'objects': [
                {
                    'authorisation': "US Coastguard",
                    'detained': True,
                    'inspection_id': "123456789012345",
                    'inspection_date': "2009-01-28",
                    'number_part_days_detained': '1.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity == Severity.OK
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': "US Coastguard",
                    'country_name': "USA",
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': True,
                    'detained_days': 1.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': "2009-01-28",
                    'port_name': "San Juan, Puerto Rico",
                },
                {
                    'authority': inspection2.authority,
                    'country_name': inspection2.country_name,
                    'defects_count': inspection2.defects_count,
                    'defects_count_severity': 'OK',
                    'detained': inspection2.detained,
                    'detained_days': inspection2.detained_days,
                    'detained_days_severity': 'OK',
                    'inspection_date': date2str(
                        inspection2.inspection_date, date_format=DATE_FORMAT),
                    'port_name': inspection2.port_name,
                },
                {
                    'authority': inspection1.authority,
                    'country_name': inspection1.country_name,
                    'defects_count': inspection1.defects_count,
                    'defects_count_severity': 'OK',
                    'detained': inspection1.detained,
                    'detained_days': inspection1.detained_days,
                    'detained_days_severity': 'OK',
                    'inspection_date': date2str(
                        inspection1.inspection_date, date_format=DATE_FORMAT),
                    'port_name': inspection1.port_name,
                },
            ],
        }

    @responses.activate
    @freeze_time("2017-09-11 07:59:00")
    def test_inspection_detained_over_24_onths_update_2_detained_in_24_months(
            self, application, factory, task, sis_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        inspection = factory.create_ship_inspection(
            ship=ship, inspection_date='2001-09-11',
            detained_days=1.0, defects_count=0,
        )

        response = {
            'objects': [
                {
                    'authorisation': "US Coastguard",
                    'detained': True,
                    'inspection_id': "123456789012345",
                    'inspection_date': "2016-06-30",
                    'number_part_days_detained': '3.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
                {
                    'authorisation': "US Coastguard",
                    'detained': True,
                    'inspection_id': "123456789012346",
                    'inspection_date': "2016-07-30",
                    'number_part_days_detained': '2.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
                {
                    'authorisation': "US Coastguard",
                    'detained': False,
                    'inspection_id': "123456789012347",
                    'inspection_date': "2016-08-30",
                    'number_part_days_detained': '0.0',
                    'no_defects': None,
                    'port_name': "San Juan, Puerto Rico",
                    'country_name': "USA",
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}inspections/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_inspections_severity ==\
            ScreeningProfile.ship_2_or_more_detained_in_24_months_severity
        assert screening.ship_inspections_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_inspections == {
            'inspections': [
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': False,
                    'detained_days': 0.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': "2016-08-30",
                    'port_name': "San Juan, Puerto Rico",
                },
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': True,
                    'detained_days': 2.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2016-07-30',
                    'port_name': 'San Juan, Puerto Rico',
                },
                {
                    'authority': 'US Coastguard',
                    'country_name': 'USA',
                    'defects_count': 0,
                    'defects_count_severity': 'OK',
                    'detained': True,
                    'detained_days': 3.0,
                    'detained_days_severity': 'OK',
                    'inspection_date': '2016-06-30',
                    'port_name': 'San Juan, Puerto Rico',
                },
                {
                    'authority': inspection.authority,
                    'country_name': inspection.country_name,
                    'defects_count': inspection.defects_count,
                    'defects_count_severity': 'OK',
                    'detained': inspection.detained,
                    'detained_days': inspection.detained_days,
                    'detained_days_severity': 'OK',
                    'inspection_date': date2str(
                        inspection.inspection_date, date_format=DATE_FORMAT),
                    'port_name': inspection.port_name,
                },
            ],
        }
