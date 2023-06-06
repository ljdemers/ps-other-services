from datetime import datetime, timedelta

import pytest

from sqlalchemy.orm.exc import NoResultFound

from screening_api.screenings.enums import Severity, Status

from screening_workers.screenings.tasks import ScreeningScreenKillerTask


class TestScreeningScreenKillerTask:

    @pytest.fixture
    def task(self, application):
        return application.tasks[ScreeningScreenKillerTask.name]

    def test_registered(self, application):
        assert ScreeningScreenKillerTask.name in application.tasks

    def test_screening_not_found(self, task):
        screening_id = 121212
        task_args = (screening_id, )

        result = task.apply(task_args)

        with pytest.raises(NoResultFound):
            result.get()

    def test_screening_completed(
            self, task, factory, application, check_tasks_mock, sis_client):
        imo_id = 9582507
        mmsi = '636015815'
        country_name = 'Liberia'
        account_id = 1234567
        ship = factory.create_ship(
            imo_id=imo_id, mmsi=mmsi, country_name=country_name)
        now = datetime.utcnow()
        updated_treshold = now - timedelta(hours=12)
        screening = factory.create_screening(
            updated=updated_treshold,
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
            zone_visits_status=Status.DONE,
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

        old_updated = screening.updated
        screening = application.screenings_repository.get_or_none(
            account_id=account_id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.updated == old_updated

        assert screening.status == Status.DONE
        assert screening.doc_company_status == Status.DONE
        assert screening.ship_technical_manager_status == Status.DONE
        assert screening.ship_manager_status == Status.DONE
        assert screening.ship_beneficial_owner_status == Status.DONE
        assert screening.ship_operator_status == Status.DONE
        assert screening.ship_registered_owner_status == Status.DONE
        assert screening.ship_flag_status == Status.DONE
        assert screening.ship_association_status == Status.DONE
        assert screening.ship_sanction_status == Status.DONE
        assert screening.port_visits_status == Status.DONE
        assert screening.ship_inspections_status == Status.DONE
        assert screening.company_sanctions_status == Status.DONE

        assert screening.ship_registered_owner_company_status ==\
            Status.DONE
        assert screening.ship_operator_company_status == Status.DONE
        assert screening.ship_beneficial_owner_company_status ==\
            Status.DONE
        assert screening.ship_manager_company_status == Status.DONE
        assert screening.ship_technical_manager_company_status ==\
            Status.DONE
        assert screening.ship_company_associates_status == Status.DONE

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

    @pytest.mark.parametrize(
        'incomplete_status', [Status.PENDING, Status.SCHEDULED],
    )
    def test_screen_screening_not_completed_no_time_treshold(
            self, task, factory, application, check_tasks_mock, sis_client,
            incomplete_status):
        imo_id = 9582507
        mmsi = '636015815'
        country_name = 'Liberia'
        account_id = 1234567
        ship = factory.create_ship(
            imo_id=imo_id, mmsi=mmsi, country_name=country_name)
        screening = factory.create_screening(
            account_id=account_id, ship=ship,

            status=incomplete_status,
            doc_company_status=incomplete_status,
            ship_technical_manager_status=incomplete_status,
            ship_manager_status=incomplete_status,
            ship_beneficial_owner_status=incomplete_status,
            ship_operator_status=incomplete_status,
            ship_registered_owner_status=incomplete_status,
            ship_flag_status=incomplete_status,
            ship_association_status=incomplete_status,
            ship_sanction_status=incomplete_status,
            port_visits_status=incomplete_status,
            zone_visits_status=incomplete_status,
            ship_inspections_status=incomplete_status,
            ship_registered_owner_company_status=incomplete_status,
            ship_operator_company_status=incomplete_status,
            ship_beneficial_owner_company_status=incomplete_status,
            ship_manager_company_status=incomplete_status,
            ship_technical_manager_company_status=incomplete_status,

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

        old_updated = screening.updated
        screening = application.screenings_repository.get_or_none(
            account_id=account_id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.updated == old_updated

        assert screening.status == incomplete_status
        assert screening.doc_company_status == incomplete_status
        assert screening.ship_technical_manager_status == incomplete_status
        assert screening.ship_manager_status == incomplete_status
        assert screening.ship_beneficial_owner_status == incomplete_status
        assert screening.ship_operator_status == incomplete_status
        assert screening.ship_registered_owner_status == incomplete_status
        assert screening.ship_flag_status == incomplete_status
        assert screening.ship_association_status == incomplete_status
        assert screening.ship_sanction_status == incomplete_status
        assert screening.port_visits_status == incomplete_status
        assert screening.ship_inspections_status == incomplete_status
        assert screening.company_sanctions_status == incomplete_status

        assert screening.ship_registered_owner_company_status ==\
            incomplete_status
        assert screening.ship_operator_company_status == incomplete_status
        assert screening.ship_beneficial_owner_company_status ==\
            incomplete_status
        assert screening.ship_manager_company_status == incomplete_status
        assert screening.ship_technical_manager_company_status ==\
            incomplete_status

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

    @pytest.mark.parametrize(
        'incomplete_status', [Status.PENDING, Status.SCHEDULED],
    )
    def test_screen_screening_not_completed_and_time_treshold(
            self, task, factory, application, check_tasks_mock, sis_client,
            incomplete_status):
        imo_id = 9582507
        mmsi = '636015815'
        country_name = 'Liberia'
        account_id = 1234567
        ship = factory.create_ship(
            imo_id=imo_id, mmsi=mmsi, country_name=country_name)
        now = datetime.utcnow()
        updated_treshold = now - timedelta(hours=12)
        screening = factory.create_screening(
            updated=updated_treshold,
            account_id=account_id, ship=ship,

            status=incomplete_status,
            doc_company_status=incomplete_status,
            ship_technical_manager_status=incomplete_status,
            ship_manager_status=incomplete_status,
            ship_beneficial_owner_status=incomplete_status,
            ship_operator_status=incomplete_status,
            ship_registered_owner_status=incomplete_status,
            ship_flag_status=incomplete_status,
            ship_association_status=incomplete_status,
            ship_sanction_status=incomplete_status,
            port_visits_status=incomplete_status,
            zone_visits_status=incomplete_status,
            ship_inspections_status=incomplete_status,
            ship_registered_owner_company_status=incomplete_status,
            ship_operator_company_status=incomplete_status,
            ship_beneficial_owner_company_status=incomplete_status,
            ship_manager_company_status=incomplete_status,
            ship_technical_manager_company_status=incomplete_status,

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

        old_updated = screening.updated
        screening = application.screenings_repository.get_or_none(
            account_id=account_id)
        assert screening is not None
        assert screening.account_id == account_id
        assert screening.updated != old_updated

        assert screening.status == Status.DONE
        assert screening.doc_company_status == Status.DONE
        assert screening.ship_technical_manager_status == Status.DONE
        assert screening.ship_manager_status == Status.DONE
        assert screening.ship_beneficial_owner_status == Status.DONE
        assert screening.ship_operator_status == Status.DONE
        assert screening.ship_registered_owner_status == Status.DONE
        assert screening.ship_flag_status == Status.DONE
        assert screening.ship_association_status == Status.DONE
        assert screening.ship_sanction_status == Status.DONE
        assert screening.port_visits_status == Status.DONE
        assert screening.ship_inspections_status == Status.DONE
        assert screening.company_sanctions_status == Status.DONE

        assert screening.ship_registered_owner_company_status ==\
            Status.DONE
        assert screening.ship_operator_company_status == Status.DONE
        assert screening.ship_beneficial_owner_company_status ==\
            Status.DONE
        assert screening.ship_manager_company_status == Status.DONE
        assert screening.ship_technical_manager_company_status ==\
            Status.DONE

        assert screening.severity == Severity.UNKNOWN
        assert screening.doc_company_severity == Severity.UNKNOWN
        assert screening.ship_technical_manager_severity == Severity.UNKNOWN
        assert screening.ship_manager_severity == Severity.UNKNOWN
        assert screening.ship_beneficial_owner_severity == Severity.UNKNOWN
        assert screening.ship_operator_severity == Severity.UNKNOWN
        assert screening.ship_registered_owner_severity == Severity.UNKNOWN
        assert screening.ship_flag_severity == Severity.UNKNOWN
        assert screening.ship_association_severity == Severity.UNKNOWN
        assert screening.ship_sanction_severity == Severity.UNKNOWN
        assert screening.port_visits_severity == Severity.UNKNOWN
        assert screening.zone_visits_severity == Severity.UNKNOWN
        assert screening.ship_inspections_severity == Severity.UNKNOWN

        assert screening.ship_registered_owner_company_severity ==\
            Severity.UNKNOWN
        assert screening.ship_operator_company_severity ==\
            Severity.UNKNOWN
        assert screening.ship_beneficial_owner_company_severity ==\
            Severity.UNKNOWN
        assert screening.ship_manager_company_severity ==\
            Severity.UNKNOWN
        assert screening.ship_technical_manager_company_severity ==\
            Severity.UNKNOWN

        ship = application.ships_repository.get_or_none(
            imo_id=imo_id)
        assert ship is not None
        assert ship.imo_id == imo_id
        assert ship.mmsi == mmsi
        assert ship.country_name == country_name
        assert screening.ship_id == ship.id
