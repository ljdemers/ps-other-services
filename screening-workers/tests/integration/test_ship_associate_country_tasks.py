from datetime import datetime
from socket import timeout

import pytest

from screening_api.screenings.enums import Severity, Status

from screening_workers.country_sanctions.enums import ShipCountryType
from screening_workers.country_sanctions.mixins import (
    ShipAssociatedCountriesMixin,
)
from screening_workers.country_sanctions.tasks import (
    ShipRegisteredOwnerCheckTask, ShipOperatorCheckTask,
    ShipBeneficialOwnerCheckTask, ShipManagerCheckTask,
    ShipTechnicalManagerCheckTask,
)


class BaseTestAssociateCountryTask:

    task_class = NotImplemented

    @pytest.fixture
    def task(self, application):
        return application.tasks[self.task_class.name]

    def test_registered(self, application):
        assert self.task_class.name in application.tasks

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

    @pytest.mark.parametrize('country_type', [
        ShipCountryType.COUNTRY_OF_DOMICILE,
        ShipCountryType.COUNTRY_OF_CONTROL,
        ShipCountryType.COUNTRY_OF_REGISTRATION,
    ])
    @pytest.mark.usefixtures('mock_task_run')
    def test_timeout(
            self, mock_task_run, application, factory, task, country_type):
        mock_task_run.side_effect = timeout
        imo_id = 12345
        account_id = 123456
        country_name = 'Atlantis'
        country_field_name = ShipAssociatedCountriesMixin.\
            get_country_field_name(task.check.associate_name, country_type)
        ship_data = {
            'imo_id': imo_id,
            country_field_name: country_name,
        }
        ship = factory.create_ship(**ship_data)
        check_status_field_name = task.check._get_check_status_field_name()
        check_severity_field_name = task.check._get_check_severity_field_name()
        screening_data = {
            'ship': ship,
            'account_id': account_id,
            check_status_field_name: Status.SCHEDULED,
            check_severity_field_name: Severity.UNKNOWN,
        }
        screening = factory.create_screening(**screening_data)

        task_args = (screening.id, )

        result = task.apply(task_args)

        with pytest.raises(timeout):
            result.get()

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert getattr(screening, check_severity_field_name) ==\
            Severity.UNKNOWN
        assert getattr(screening, check_status_field_name) == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is None

    @pytest.mark.parametrize('country_type', [
        ShipCountryType.COUNTRY_OF_DOMICILE,
        ShipCountryType.COUNTRY_OF_CONTROL,
        ShipCountryType.COUNTRY_OF_REGISTRATION,
    ])
    def test_no_sanctions(
            self, application, factory, task, ship_update_cache, country_type):
        imo_id = 12345
        account_id = 123456
        country_name = 'Atlantis'
        country_field_name = ShipAssociatedCountriesMixin.\
            get_country_field_name(task.check.associate_name, country_type)
        ship_data = {
            'imo_id': imo_id,
            country_field_name: country_name,
            'length': 123.4,
            'breadth': 234.5,
            'displacement': 345.6,
            'draught': 456.7,
        }
        ship = factory.create_ship(**ship_data)
        ship_extended = ShipAssociatedCountriesMixin(ship)
        check_status_field_name = task.check._get_check_status_field_name()
        check_severity_field_name = task.check._get_check_severity_field_name()
        screening_data = {
            'ship': ship,
            'account_id': account_id,
            check_status_field_name: Status.SCHEDULED,
            check_severity_field_name: Severity.UNKNOWN,
        }
        screening = factory.create_screening(**screening_data)
        ship_update_cache.put(str(ship.id), datetime.utcnow())

        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert getattr(screening, check_severity_field_name) == Severity.OK
        assert getattr(screening, check_status_field_name) == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        check_report_field_name = task.check._get_check_report_field_name()
        check_report = getattr(report, check_report_field_name)
        company = ship_extended.get_company(task.check.associate_name)
        assert check_report['company'] == company
        assert check_report[country_type.value] == country_name
        severity_field = '{0}_severity'.format(country_type.value)
        assert check_report[severity_field] == Severity.OK.name

    @pytest.mark.parametrize('country_type', [
        ShipCountryType.COUNTRY_OF_DOMICILE,
        ShipCountryType.COUNTRY_OF_CONTROL,
        ShipCountryType.COUNTRY_OF_REGISTRATION,
    ])
    def test_unknown_country(
            self, application, factory, task, ship_update_cache, country_type):
        imo_id = 12345
        account_id = 123456
        country_name = None
        country_field_name = ShipAssociatedCountriesMixin.\
            get_country_field_name(task.check.associate_name, country_type)
        ship_data = {
            'imo_id': imo_id,
            country_field_name: country_name,
        }
        ship = factory.create_ship(**ship_data)
        ship_extended = ShipAssociatedCountriesMixin(ship)
        check_status_field_name = task.check._get_check_status_field_name()
        check_severity_field_name = task.check._get_check_severity_field_name()
        screening_data = {
            'ship': ship,
            'account_id': account_id,
            check_status_field_name: Status.SCHEDULED,
            check_severity_field_name: Severity.UNKNOWN,
        }
        screening = factory.create_screening(**screening_data)
        ship_update_cache.put(str(ship.id), datetime.utcnow())

        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert getattr(screening, check_severity_field_name) ==\
            Severity.OK
        assert getattr(screening, check_status_field_name) == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        check_report_field_name = task.check._get_check_report_field_name()
        check_report = getattr(report, check_report_field_name)
        company = ship_extended.get_company(task.check.associate_name)
        assert check_report['company'] == company
        assert check_report[country_type.value] == country_name
        severity_field = '{0}_severity'.format(country_type.value)
        assert check_report[severity_field] == Severity.OK.name

    @pytest.mark.parametrize('country_type', [
        ShipCountryType.COUNTRY_OF_DOMICILE,
        ShipCountryType.COUNTRY_OF_CONTROL,
        ShipCountryType.COUNTRY_OF_REGISTRATION,
    ])
    def test_blacklisted(
            self, application, factory, task, ship_update_cache, country_type):
        imo_id = 12345
        account_id = 123456
        country_name = 'Atlantis'
        country_field_name = ShipAssociatedCountriesMixin.\
            get_country_field_name(task.check.associate_name, country_type)
        ship_data = {
            'imo_id': imo_id,
            country_field_name: country_name,
        }
        ship = factory.create_ship(**ship_data)
        ship_extended = ShipAssociatedCountriesMixin(ship)
        check_status_field_name = task.check._get_check_status_field_name()
        check_severity_field_name = task.check._get_check_severity_field_name()
        screening_data = {
            'ship': ship,
            'account_id': account_id,
            check_status_field_name: Status.SCHEDULED,
            check_severity_field_name: Severity.UNKNOWN,
        }
        screening = factory.create_screening(**screening_data)
        ship_update_cache.put(str(ship.id), datetime.utcnow())
        blacklist_data = {
            'country_name': country_name,
        }
        blacklist = factory.create_blacklisted_country(**blacklist_data)

        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        assert screening is not None
        assert screening.account_id == account_id
        assert getattr(screening, check_severity_field_name) ==\
            blacklist.severity
        assert getattr(screening, check_status_field_name) == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        check_report_field_name = task.check._get_check_report_field_name()
        check_report = getattr(report, check_report_field_name)
        company = ship_extended.get_company(task.check.associate_name)
        assert check_report['company'] == company
        assert check_report[country_type.value] == country_name
        severity_field = '{0}_severity'.format(country_type.value)
        assert check_report[severity_field] == blacklist.severity.name


class TestShipRegisteredOwnerCheckTask(BaseTestAssociateCountryTask):

    task_class = ShipRegisteredOwnerCheckTask


class TestShipOperatorCheckTask(BaseTestAssociateCountryTask):

    task_class = ShipOperatorCheckTask


class TestShipBeneficialOwnerCheckTask(BaseTestAssociateCountryTask):

    task_class = ShipBeneficialOwnerCheckTask


class TestShipManagerCheckTask(BaseTestAssociateCountryTask):

    task_class = ShipManagerCheckTask


class TestShipTechnicalManagerCheckTask(BaseTestAssociateCountryTask):

    task_class = ShipTechnicalManagerCheckTask
