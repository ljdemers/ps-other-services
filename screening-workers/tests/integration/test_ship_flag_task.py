from datetime import datetime
from socket import timeout

import pytest

from screening_api.screenings.enums import Severity, Status

from screening_workers.country_sanctions.tasks import ShipFlagCheckTask


class TestShipFlagCheckTask:

    @pytest.fixture
    def task(self, application):
        return application.tasks[ShipFlagCheckTask.name]

    def test_registered(self, application):
        assert ShipFlagCheckTask.name in application.tasks

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
    def test_timeout(self, mock_task_run, application, factory, task):
        mock_task_run.side_effect = timeout
        imo_id = 12345
        account_id = 123456
        country_name = 'Atlantis'
        ship = factory.create_ship(
            imo_id=imo_id, country_name=country_name)
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
        assert screening.ship_flag_severity == Severity.UNKNOWN
        assert screening.ship_flag_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is None

    def test_no_sanctions(self, application, factory, task, ship_update_cache):
        imo_id = 12345
        account_id = 123456
        country_name = 'Atlantis'
        ship = factory.create_ship(
            imo_id=imo_id, country_name=country_name, length=123.4,
            breadth=234.5, displacement=345.6, draught=456.7,
        )
        screening = factory.create_screening(
            ship=ship, account_id=account_id,
            severity=Severity.UNKNOWN, status=Status.SCHEDULED,
        )
        ship_update_cache.put(str(ship.id), datetime.utcnow())

        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_flag_severity == Severity.OK
        assert screening.ship_flag_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_flag == {
            'country': ship.country_name,
            'severity': Severity.OK.name,
        }
        assert report.ship_info == {
            'name': ship.name,
            'imo': ship.imo,
            'type': ship.type,
            'build_year': ship.build_year,
            'build_age': ship.build_age,
            'build_age_severity': ship.build_age_severity.name,
            'country_name': ship.country_name,
            'country_id': ship.country_id,
            'flag_effective_date': ship.flag_effective_date,
            'mmsi': ship.mmsi,
            'call_sign': ship.call_sign,
            'status': 'In Service/Commission',
            'port_of_registry': ship.port_of_registry,
            'deadweight': ship.deadweight,
            'weight': ship.weight,
            'length': float(ship.length),
            'breadth': float(ship.breadth),
            'displacement': float(ship.displacement),
            'draught': float(ship.draught),
            'registered_owner': ship.registered_owner,
            'operator': ship.operator,
            'group_beneficial_owner': ship.group_beneficial_owner,
            'ship_manager': ship.ship_manager,
            'technical_manager': ship.technical_manager,
            'shipbuilder': ship.shipbuilder,
            'build_country_name': ship.build_country_name,
            'classification_society': ship.classification_society,
        }

    def test_blacklisted(self, application, factory, task, ship_update_cache):
        imo_id = 12345
        account_id = 123456
        country_name = 'Atlantis'
        ship = factory.create_ship(
            imo_id=imo_id, country_name=country_name)
        screening = factory.create_screening(
            ship=ship, account_id=account_id,
            severity=Severity.UNKNOWN, status=Status.SCHEDULED,
        )
        ship_update_cache.put(str(ship.id), datetime.utcnow())
        blacklist = factory.create_blacklisted_country(
            country_name=country_name,
        )

        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.ship_flag_severity == blacklist.severity
        assert screening.ship_flag_status == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        assert report.ship_flag == {
            'country': ship.country_name,
            'severity': blacklist.severity.name,
        }
