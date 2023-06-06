import pytest

from screening_api.ships.repositories import ShipsRepository


class TestShipsRepositoryUpdateOrCreate:

    @pytest.fixture
    def repository(self, session_factory):
        return ShipsRepository(session_factory)

    def test_create(self, repository):
        imo_id = 12345
        mmsi = '999999'
        data = {
            'mmsi': mmsi,
        }

        result = repository.update_or_create(imo_id, **data)

        assert result[1]
        assert result[0].imo_id == imo_id
        assert result[0].mmsi == mmsi

    def test_update(self, repository, factory):
        imo_id = 12345
        ship = factory.create_ship(imo_id=imo_id, mmsi='111111')
        mmsi = '999999'
        data = {
            'mmsi': mmsi,
        }

        result = repository.update_or_create(imo_id, **data)

        assert not result[1]
        assert result[0].id == ship.id
        assert result[0].imo_id == imo_id
        assert result[0].mmsi == mmsi
