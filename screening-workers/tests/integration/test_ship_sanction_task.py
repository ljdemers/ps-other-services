from datetime import datetime
import json
from socket import timeout

import pytest
import responses

from screening_api.screenings.enums import Severity, Status

from screening_workers.ship_sanctions.tasks import ShipSanctionCheckTask


class TestShipSanctionsTask:

    @pytest.fixture
    def task(self, application):
        return application.tasks[ShipSanctionCheckTask.name]

    def test_registered(self, application):
        assert ShipSanctionCheckTask.name in application.tasks

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
            self, mock_task_run, application, factory, task):
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
        assert screening.ship_sanction_severity == Severity.UNKNOWN
        assert screening.ship_sanction_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is None

    @responses.activate
    def test_no_sanctions(
            self, application, factory, task, compliance_client):
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
            'results': [],
        }
        responses.add(
            responses.GET,
            '{0}ships/?imo_number={1}'.format(
                compliance_client.base_uri, imo_id),
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
        assert screening.ship_sanction_severity == Severity.OK
        assert screening.ship_sanction_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_sanction == {
            'sanctions': [],
        }

    @responses.activate
    def test_no_sanctions_no_update(
            self, application, factory, task, ship_sanctions_update_cache):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        ship_sanctions_update_cache.put(str(ship.id), datetime.utcnow())
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_sanction_severity == Severity.OK
        assert screening.ship_sanction_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_sanction == {
            'sanctions': [],
        }

    @responses.activate
    def test_no_sanctions_update_sanction(
            self, application, factory, task, compliance_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)

        response = {
            'results': [
                {
                    'id': 1752885,
                    'status': 'Active',
                    'name': ship.name,
                    'imo_number': ship.imo_id,
                    'ship_sanctions': [
                        {
                            'sanction': {
                                'code': '2',
                                'name': 'OFAC - WMD Supporters List',
                                'status': 'Active',
                            },
                            'id': 123,
                            'status': 'Active',
                            'since_date': '2001-09-11',
                            'to_date': '2001-09-12',
                        },
                    ],
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}ships/?imo_number={1}&limit=1'.format(
                compliance_client.base_uri, imo_id),
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
        assert screening.ship_sanction_severity == Severity.CRITICAL
        assert screening.ship_sanction_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_sanction == {
            'sanctions': [
                {
                    'sanction_name': 'OFAC - WMD Supporters List',
                    'listed_since': '2001-09-11T00:00:00Z',
                    'listed_to': '2001-09-12T00:00:00Z',
                    'sanction_severity': 'CRITICAL',
                },
            ],
        }

    @responses.activate
    def test_no_sanctions_update_blacklisted_sanction(
            self, application, factory, task, compliance_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        blacklisted_code = 2
        factory.create_blacklisted_sanction_list(
            id=1,
            sanction_codes={
                blacklisted_code: {},
            },
         )

        response = {
            'results': [
                {
                    'id': 1752885,
                    'status': 'Active',
                    'name': ship.name,
                    'imo_number': ship.imo_id,
                    'ship_sanctions': [
                        {
                            'sanction': {
                                'code': blacklisted_code,
                                'name': 'OFAC - WMD Supporters List',
                                'status': 'Active',
                            },
                            'id': 123,
                            'status': 'Active',
                            'since_date': '2001-09-11',
                            'to_date': '2001-09-12',
                        },
                    ],
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}ships/?imo_number={1}&limit=1'.format(
                compliance_client.base_uri, imo_id),
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
        assert screening.ship_sanction_severity == Severity.OK
        assert screening.ship_sanction_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_sanction == {
            'sanctions': [],
        }

    @responses.activate
    def test_sanctions_update_no_sanction(
            self, application, factory, task, compliance_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        factory.create_ship_sanction(
            ship=ship, start_date='2001-09-11T00:00:00Z', end_date=None,
            sanction_list_name='OFAC - WMD Supporters List', is_active=True,
        )

        response = {
            'results': [
                {
                    'id': 1752885,
                    'status': 'Active',
                    'name': ship.name,
                    'imo_number': ship.imo_id,
                    'ship_sanctions': [],
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}ships/?imo_number={1}&limit=1'.format(
                compliance_client.base_uri, imo_id),
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
        assert screening.ship_sanction_severity == Severity.CRITICAL
        assert screening.ship_sanction_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_sanction == {
            'sanctions': [
                {
                    'sanction_name': 'OFAC - WMD Supporters List',
                    'listed_since': '2001-09-11T00:00:00Z',
                    'listed_to': None,
                    'sanction_severity': 'CRITICAL',
                },
            ],
        }

    @responses.activate
    def test_sanctions_update_sanction_expired(
            self, application, factory, task, compliance_client):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(ship=ship, account_id=account_id)
        sanction = factory.create_ship_sanction(
            ship=ship, end_date=None, is_active=True,
            sanction_list_name='OFAC - WMD Supporters List',
        )

        response = {
            'results': [
                {
                    'id': 1752885,
                    'status': 'Active',
                    'name': ship.name,
                    'imo_number': ship.imo_id,
                    'ship_sanctions': [
                        {
                            'sanction': {
                                'code': 2,
                                'name': sanction.sanction_list_name,
                                'status': 'Suspended',
                            },
                            'id': 123,
                            'status': 'INACTIVE',
                            'since_date': '2001-09-11',
                            'to_date': '2001-09-12',
                        },
                    ],
                },
            ],
        }
        responses.add(
            responses.GET,
            '{0}ships/?imo_number={1}&limit=1'.format(
                compliance_client.base_uri, imo_id),
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
        assert screening.ship_sanction_severity == Severity.OK
        assert screening.ship_sanction_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_sanction == {
            'sanctions': [
                {
                    'listed_since': '2001-09-11T00:00:00Z',
                    'listed_to': '2001-09-12T00:00:00Z',
                    'sanction_name': 'OFAC - WMD Supporters List',
                    'sanction_severity': 'OK',
                },
            ],
        }
