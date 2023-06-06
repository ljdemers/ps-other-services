import pytest

from screening_workers.ships.tasks import ShipsCacheUpdateTask


class TestShipsCacheUpdateTask:

    @pytest.fixture
    def task(self, application):
        return application.tasks[ShipsCacheUpdateTask.name]

    def test_registered(self, application):
        assert ShipsCacheUpdateTask.name in application.tasks
