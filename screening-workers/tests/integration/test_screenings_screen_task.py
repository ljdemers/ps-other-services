import pytest

from sqlalchemy.orm.exc import NoResultFound

from screening_api.screenings.enums import Severity, Status

from screening_workers.screenings.tasks import ScreeningScreenTask


class TestScreeningScreenTask:

    @pytest.fixture
    def task(self, application):
        return application.tasks[ScreeningScreenTask.name]

    def test_registered(self, application):
        assert ScreeningScreenTask.name in application.tasks

    def test_screening_not_found(self, task):
        screening_id = 121212
        task_args = (screening_id, )

        result = task.apply(task_args)

        with pytest.raises(NoResultFound):
            result.get()

    def test_screen(
            self, task, factory, application, check_tasks_mock, sis_client):
        imo_id = 9582507
        mmsi = '636015815'
        country_name = 'Liberia'
        account_id = 1234567
        ship = factory.create_ship(
            imo_id=imo_id, mmsi=mmsi, country_name=country_name)
        screening = factory.create_screening(
            account_id=account_id, ship=ship,

            status=Status.DONE,
            doc_company_status=Status.DONE,
            ship_technical_manager_status=Status.DONE,
            ship_manager_status=Status.DONE,
            ship_beneficial_owner_status=Status.DONE,
            ship_operator_status=Status.DONE,
            ship_registered_owner_status=Status.DONE,
            ship_flag_status=Status.DONE,
            ship_association_status=Status.DONE,
            ship_sanction_status=Status.DONE,
            port_visits_status=Status.DONE,
            ship_inspections_status=Status.DONE,
            ship_registered_owner_company_status=Status.DONE,
            ship_operator_company_status=Status.DONE,
            ship_beneficial_owner_company_status=Status.DONE,
            ship_manager_company_status=Status.DONE,
            ship_technical_manager_company_status=Status.DONE,
            ship_company_associates_status=Status.DONE,

            severity=Severity.OK,
            doc_company_severity=Severity.OK,
            ship_technical_manager_severity=Severity.OK,
            ship_manager_severity=Severity.OK,
            ship_beneficial_owner_severity=Severity.OK,
            ship_operator_severity=Severity.OK,
            ship_registered_owner_severity=Severity.OK,
            ship_flag_severity=Severity.OK,
            ship_association_severity=Severity.OK,
            ship_sanction_severity=Severity.OK,
            port_visits_severity=Severity.OK,
            zone_visits_severity=Severity.OK,
            ship_inspections_severity=Severity.OK,
            ship_registered_owner_company_severity=Severity.OK,
            ship_operator_company_severity=Severity.OK,
            ship_beneficial_owner_company_severity=Severity.OK,
            ship_manager_company_severity=Severity.OK,
            ship_technical_manager_company_severity=Severity.OK,
            ship_company_associates_severity=Severity.OK,
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            account_id=account_id)
        assert screening is not None
        assert screening.account_id == account_id

        assert screening.status == Status.SCHEDULED
        assert screening.doc_company_status == Status.SCHEDULED
        assert screening.ship_technical_manager_status == Status.SCHEDULED
        assert screening.ship_manager_status == Status.SCHEDULED
        assert screening.ship_beneficial_owner_status == Status.SCHEDULED
        assert screening.ship_operator_status == Status.SCHEDULED
        assert screening.ship_registered_owner_status == Status.SCHEDULED
        assert screening.ship_flag_status == Status.SCHEDULED
        assert screening.ship_association_status == Status.SCHEDULED
        assert screening.ship_sanction_status == Status.SCHEDULED
        assert screening.port_visits_status == Status.SCHEDULED
        assert screening.ship_inspections_status == Status.SCHEDULED
        assert screening.company_sanctions_status == Status.SCHEDULED

        assert screening.ship_registered_owner_company_status ==\
            Status.SCHEDULED
        assert screening.ship_operator_company_status == Status.SCHEDULED
        assert screening.ship_beneficial_owner_company_status ==\
            Status.SCHEDULED
        assert screening.ship_manager_company_status == Status.SCHEDULED
        assert screening.ship_technical_manager_company_status ==\
            Status.SCHEDULED
        assert screening.ship_company_associates_status == Status.SCHEDULED

        assert screening.severity == Severity.OK
        assert screening.doc_company_severity == Severity.OK
        assert screening.ship_technical_manager_severity == Severity.OK
        assert screening.ship_manager_severity == Severity.OK
        assert screening.ship_beneficial_owner_severity == Severity.OK
        assert screening.ship_operator_severity == Severity.OK
        assert screening.ship_registered_owner_severity == Severity.OK
        assert screening.ship_flag_severity == Severity.OK
        assert screening.ship_association_severity == Severity.OK
        assert screening.ship_sanction_severity == Severity.OK
        assert screening.port_visits_severity == Severity.OK
        assert screening.zone_visits_severity == Severity.OK
        assert screening.ship_inspections_severity == Severity.OK

        assert screening.ship_registered_owner_company_severity ==\
            Severity.OK
        assert screening.ship_operator_company_severity == Severity.OK
        assert screening.ship_beneficial_owner_company_severity ==\
            Severity.OK
        assert screening.ship_manager_company_severity == Severity.OK
        assert screening.ship_technical_manager_company_severity ==\
            Severity.OK
        assert screening.ship_company_associates_severity == Severity.OK

        ship = application.ships_repository.get_or_none(
            imo_id=imo_id)
        assert ship is not None
        assert ship.imo_id == imo_id
        assert ship.mmsi == mmsi
        assert ship.country_name == country_name
        assert screening.ship_id == ship.id

        args = (screening.id, )
        check_tasks_mock.doc_company_task.assert_called_once_with(args)
        check_tasks_mock.ship_technical_manager_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_manager_task.assert_called_once_with(args)
        check_tasks_mock.ship_beneficial_owner_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_operator_task.assert_called_once_with(args)
        check_tasks_mock.ship_registered_owner_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_flag_task.assert_called_once_with(args)
        check_tasks_mock.ship_flag_task.assert_called_once_with(args)
        check_tasks_mock.ship_association_task.assert_called_once_with(args)
        check_tasks_mock.ship_sanction_task.assert_called_once_with(args)
        check_tasks_mock.port_visits_task.assert_called_once_with(args)
        check_tasks_mock.zone_visits_task.assert_called_once_with(args)
        check_tasks_mock.ship_inspections_task.assert_called_once_with(args)

        check_tasks_mock.ship_reg_owner_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_operator_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_beneficial_owner_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_manager_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_technical_manager_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_company_associates_task.\
            assert_called_once_with(args)

        history = application.screenings_history_repository.get_or_none(
            screening_id=screening.id)
        assert history is not None
        assert history.screening_id == screening.id
        assert history.severity == Severity.OK
        assert history.doc_company_severity == Severity.OK
        assert history.ship_technical_manager_severity == Severity.OK
        assert history.ship_manager_severity == Severity.OK
        assert history.ship_beneficial_owner_severity == Severity.OK
        assert history.ship_operator_severity == Severity.OK
        assert history.ship_registered_owner_severity == Severity.OK
        assert history.ship_flag_severity == Severity.OK
        assert history.ship_association_severity == Severity.OK
        assert history.ship_sanction_severity == Severity.OK
        assert history.port_visits_severity == Severity.OK
        assert history.zone_visits_severity == Severity.OK
        assert history.ship_inspections_severity == Severity.OK
        assert history.ship_registered_owner_company_severity == Severity.OK
        assert history.ship_operator_company_severity == Severity.OK
        assert history.ship_beneficial_owner_company_severity == Severity.OK
        assert history.ship_manager_company_severity == Severity.OK
        assert history.ship_technical_manager_company_severity == Severity.OK
        assert history.ship_company_associates_severity == Severity.OK

    def test_screen_screening_not_completed(
            self, task, factory, application, check_tasks_mock, sis_client):
        imo_id = 9582507
        mmsi = '636015815'
        country_name = 'Liberia'
        account_id = 1234567
        ship = factory.create_ship(
            imo_id=imo_id, mmsi=mmsi, country_name=country_name)
        screening = factory.create_screening(
            account_id=account_id, ship=ship,

            status=Status.PENDING,
            doc_company_status=Status.PENDING,
            ship_technical_manager_status=Status.PENDING,
            ship_manager_status=Status.PENDING,
            ship_beneficial_owner_status=Status.PENDING,
            ship_operator_status=Status.PENDING,
            ship_registered_owner_status=Status.PENDING,
            ship_flag_status=Status.PENDING,
            ship_association_status=Status.PENDING,
            ship_sanction_status=Status.PENDING,
            port_visits_status=Status.PENDING,
            ship_inspections_status=Status.PENDING,
            ship_registered_owner_company_status=Status.PENDING,
            ship_operator_company_status=Status.PENDING,
            ship_beneficial_owner_company_status=Status.PENDING,
            ship_manager_company_status=Status.PENDING,
            ship_technical_manager_company_status=Status.PENDING,

            severity=Severity.OK,
            doc_company_severity=Severity.OK,
            ship_technical_manager_severity=Severity.OK,
            ship_manager_severity=Severity.OK,
            ship_beneficial_owner_severity=Severity.OK,
            ship_operator_severity=Severity.OK,
            ship_registered_owner_severity=Severity.OK,
            ship_flag_severity=Severity.OK,
            ship_association_severity=Severity.OK,
            ship_sanction_severity=Severity.OK,
            port_visits_severity=Severity.OK,
            zone_visits_severity=Severity.OK,
            ship_inspections_severity=Severity.OK,
            ship_registered_owner_company_severity=Severity.OK,
            ship_operator_company_severity=Severity.OK,
            ship_beneficial_owner_company_severity=Severity.OK,
            ship_manager_company_severity=Severity.OK,
            ship_technical_manager_company_severity=Severity.OK,
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            account_id=account_id)
        assert screening is not None
        assert screening.account_id == account_id

        assert screening.status == Status.PENDING
        assert screening.doc_company_status == Status.PENDING
        assert screening.ship_technical_manager_status == Status.PENDING
        assert screening.ship_manager_status == Status.PENDING
        assert screening.ship_beneficial_owner_status == Status.PENDING
        assert screening.ship_operator_status == Status.PENDING
        assert screening.ship_registered_owner_status == Status.PENDING
        assert screening.ship_flag_status == Status.PENDING
        assert screening.ship_association_status == Status.PENDING
        assert screening.ship_sanction_status == Status.PENDING
        assert screening.port_visits_status == Status.PENDING
        assert screening.ship_inspections_status == Status.PENDING
        assert screening.company_sanctions_status == Status.PENDING

        assert screening.ship_registered_owner_company_status ==\
            Status.PENDING
        assert screening.ship_operator_company_status == Status.PENDING
        assert screening.ship_beneficial_owner_company_status ==\
            Status.PENDING
        assert screening.ship_manager_company_status == Status.PENDING
        assert screening.ship_technical_manager_company_status ==\
            Status.PENDING

        assert screening.severity == Severity.OK
        assert screening.doc_company_severity == Severity.OK
        assert screening.ship_technical_manager_severity == Severity.OK
        assert screening.ship_manager_severity == Severity.OK
        assert screening.ship_beneficial_owner_severity == Severity.OK
        assert screening.ship_operator_severity == Severity.OK
        assert screening.ship_registered_owner_severity == Severity.OK
        assert screening.ship_flag_severity == Severity.OK
        assert screening.ship_association_severity == Severity.OK
        assert screening.ship_sanction_severity == Severity.OK
        assert screening.port_visits_severity == Severity.OK
        assert screening.zone_visits_severity == Severity.OK
        assert screening.ship_inspections_severity == Severity.OK

        assert screening.ship_registered_owner_company_severity ==\
            Severity.OK
        assert screening.ship_operator_company_severity == Severity.OK
        assert screening.ship_beneficial_owner_company_severity ==\
            Severity.OK
        assert screening.ship_manager_company_severity == Severity.OK
        assert screening.ship_technical_manager_company_severity ==\
            Severity.OK

        ship = application.ships_repository.get_or_none(
            imo_id=imo_id)
        assert ship is not None
        assert ship.imo_id == imo_id
        assert ship.mmsi == mmsi
        assert ship.country_name == country_name
        assert screening.ship_id == ship.id

        assert not check_tasks_mock.doc_company_task.called
        assert not check_tasks_mock.ship_technical_manager_task.called
        assert not check_tasks_mock.ship_manager_task.called
        assert not check_tasks_mock.ship_beneficial_owner_task.called
        assert not check_tasks_mock.ship_operator_task.called
        assert not check_tasks_mock.ship_registered_owner_task.called
        assert not check_tasks_mock.ship_flag_task.called
        assert not check_tasks_mock.ship_flag_task.called
        assert not check_tasks_mock.ship_association_task.called
        assert not check_tasks_mock.ship_sanction_task.called
        assert not check_tasks_mock.port_visits_task.called
        assert not check_tasks_mock.zone_visits_task.called
        assert not check_tasks_mock.ship_inspections_task.called

        assert not check_tasks_mock.ship_reg_owner_company_task.called
        assert not check_tasks_mock.ship_operator_company_task.called
        assert not check_tasks_mock.ship_beneficial_owner_company_task.called
        assert not check_tasks_mock.ship_manager_company_task.called
        assert not check_tasks_mock.ship_technical_manager_company_task.called
