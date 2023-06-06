import pytest

from screening_workers.screenings.tasks import ScreeningsBulkScreenTask


class TestBulkScreeningValidationTask:

    @pytest.fixture
    def schedule(self, application):
        return application._conf.beat_schedule[ScreeningsBulkScreenTask.name]

    def test_registered(self, application):
        assert ScreeningsBulkScreenTask.name in application._conf.beat_schedule

    def test_frequency(self, schedule):
        assert schedule['schedule'].minute == set([0])
        assert schedule['schedule'].hour == set([1])
