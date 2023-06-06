import pytest

from screening_workers.screenings.tasks import ScreeningsBulkScreenKillerTask


class TestScreeningsBulkScreenKillerTaskSchedule:

    @pytest.fixture
    def schedule(self, application):
        return application._conf.beat_schedule[
            ScreeningsBulkScreenKillerTask.name]

    def test_registered(self, application):
        assert ScreeningsBulkScreenKillerTask.name \
            in application._conf.beat_schedule

    def test_frequency(self, schedule):
        assert schedule['schedule'].minute == set([0])
        assert schedule['schedule'].hour == set([0])
