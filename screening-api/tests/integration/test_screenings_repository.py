from unittest import mock

import pytest

from screening_api.screenings.enums import Severity, Status, SeverityChange
from screening_api.screenings.models import Screening
from screening_api.screenings.repositories import ScreeningsRepository


class TestScreeningsRepositoryUpdate:

    @pytest.fixture
    def repository(self, session_factory):
        return ScreeningsRepository(session_factory)

    @pytest.yield_fixture
    def mock_calculated_status(self):
        with mock.patch.object(Screening, 'get_calculated_status') as m:
            yield m

    @pytest.yield_fixture
    def mock_calculated_severity(self):
        with mock.patch.object(Screening, 'get_calculated_severity') as m:
            yield m

    @pytest.yield_fixture
    def mock_calculated_severity_change(self):
        with mock.patch.object(
                Screening, 'get_calculated_severity_change') as m:
            yield m

    @pytest.mark.parametrize('old_status, new_status', [
        (Status.CREATED, Status.CREATED),
        (Status.CREATED, Status.SCHEDULED),
        (Status.SCHEDULED, Status.SCHEDULED),
        (Status.SCHEDULED, Status.PENDING),
        (Status.PENDING, Status.PENDING),
        (Status.DONE, Status.DONE),
        (Status.DONE, Status.SCHEDULED),
    ])
    def test_severity_no_change(
            self, repository, factory, old_status, new_status,
            mock_calculated_severity, mock_calculated_severity_change,
            mock_calculated_status):
        new_severity = Severity.OK
        new_severity_change = SeverityChange.DECREASED
        mock_calculated_severity.return_value = new_severity
        mock_calculated_severity_change.return_value = new_severity_change
        mock_calculated_status.return_value = new_status
        ship = factory.create_ship()
        screening = factory.create_screening(
            ship=ship,
            status=old_status, severity_change=SeverityChange.INCREASED,
            previous_severity=Severity.WARNING, severity=Severity.CRITICAL,
        )

        result = repository.update(screening.id)

        assert result.previous_severity == screening.previous_severity
        assert result.previous_severity_date ==\
            screening.previous_severity_date
        assert result.severity == screening.severity
        assert result.severity_change == screening.severity_change

    @pytest.mark.parametrize('old_status, new_status', [
        (Status.CREATED, Status.DONE),
        (Status.SCHEDULED, Status.DONE),
        (Status.PENDING, Status.DONE),
    ])
    def test_severity_recalculated(
            self, repository, factory, old_status, new_status,
            mock_calculated_severity, mock_calculated_severity_change,
            mock_calculated_status):
        new_severity = Severity.OK
        new_severity_change = SeverityChange.DECREASED
        mock_calculated_severity.return_value = new_severity
        mock_calculated_severity_change.return_value = new_severity_change
        mock_calculated_status.return_value = new_status
        ship = factory.create_ship()
        screening = factory.create_screening(
            ship=ship,
            status=old_status, severity_change=SeverityChange.INCREASED,
            previous_severity=Severity.WARNING, severity=Severity.CRITICAL,
        )

        result = repository.update(screening.id)

        assert result.previous_severity == screening.severity
        assert result.previous_severity_date == screening.updated
        assert result.severity == new_severity
        assert result.severity_change == new_severity_change
