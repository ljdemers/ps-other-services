import pytest

from screening_api.screenings.enums import Status, Severity

from screening_workers.screenings_history.creators import (
    ScreeningsHistoryCreator,
)


class TestScreeningsHistoryCreator:

    @pytest.fixture
    def creator(self, application):
        return ScreeningsHistoryCreator(
            application.screenings_repository,
            application.screenings_history_repository,
            application.screenings_reports_repository
        )

    @pytest.mark.parametrize('status', [
        Status.CREATED, Status.SCHEDULED, Status.PENDING,
    ])
    def test_not_done_screening(
            self, factory, creator, application, status):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        screening = factory.create_screening(
            ship=ship, account_id=account_id, status=status)

        creator.create(screening.id)

        screening_history = application.screenings_history_repository.\
            get_or_none(screening_id=screening.id)

        assert screening_history is None

    def test_done_screening(
            self, factory, creator, application):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')

        port_visits = {
            'ihs_movement_data': [1],
            'port_visits': [1, 2],
        }

        screening = factory.create_screening(
            ship=ship, account_id=account_id, status=Status.DONE,
            doc_company_severity=Severity.WARNING,
            ship_technical_manager_severity=Severity.OK,
            ship_manager_severity=Severity.UNKNOWN,
            ship_beneficial_owner_severity=Severity.OK,
            ship_operator_severity=Severity.OK,
            ship_registered_owner_severity=Severity.CRITICAL,
            ship_flag_severity=Severity.OK,
            ship_association_severity=Severity.WARNING,
            ship_sanction_severity=Severity.OK,
            port_visits_severity=Severity.UNKNOWN,
            zone_visits_severity=Severity.OK,
            ship_inspections_severity=Severity.CRITICAL,

            ship_registered_owner_company_severity=Severity.OK,
            ship_operator_company_severity=Severity.WARNING,
            ship_beneficial_owner_company_severity=Severity.CRITICAL,
            ship_manager_company_severity=Severity.OK,
            ship_technical_manager_company_severity=Severity.WARNING,
        )

        report = factory.create_screening_report(
            screening=screening, port_visits=port_visits)

        creator.create(screening.id)

        screening_history = application.screenings_history_repository.\
            get_or_none(screening_id=screening.id)

        assert screening_history is not None
        assert screening_history.screening_id == screening.id
        assert screening_history.doc_company_severity == \
            screening.doc_company_severity
        assert screening_history.ship_technical_manager_severity == \
            screening.ship_technical_manager_severity
        assert screening_history.ship_manager_severity == \
            screening.ship_manager_severity
        assert screening_history.ship_beneficial_owner_severity == \
            screening.ship_beneficial_owner_severity
        assert screening_history.ship_operator_severity == \
            screening.ship_operator_severity
        assert screening_history.ship_registered_owner_severity == \
            screening.ship_registered_owner_severity
        assert screening_history.ship_flag_severity == \
            screening.ship_flag_severity
        assert screening_history.ship_association_severity == \
            screening.ship_association_severity
        assert screening_history.ship_sanction_severity == \
            screening.ship_sanction_severity
        assert screening_history.port_visits_severity == \
            screening.port_visits_severity
        assert screening_history.zone_visits_severity == \
            screening.zone_visits_severity
        assert screening_history.ship_inspections_severity == \
            screening.ship_inspections_severity
        assert screening_history.ship_registered_owner_company_severity == \
            screening.ship_registered_owner_company_severity
        assert screening_history.ship_operator_company_severity == \
            screening.ship_operator_company_severity
        assert screening_history.ship_beneficial_owner_company_severity == \
            screening.ship_beneficial_owner_company_severity
        assert screening_history.ship_manager_company_severity == \
            screening.ship_manager_company_severity
        assert screening_history.ship_technical_manager_company_severity == \
            screening.ship_technical_manager_company_severity

        assert screening_history.ship_info == report.ship_info
        assert screening_history.port_visits == report.port_visits
