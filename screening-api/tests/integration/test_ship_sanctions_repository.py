import pytest

from screening_api.ship_sanctions.repositories import ShipSanctionsRepository


class TestShipSanctionsRepositoryFind:

    @pytest.fixture
    def repository(self, session_factory):
        return ShipSanctionsRepository(session_factory)

    def test_no_sanctions(self, repository):
        ship_id = 1

        result = repository.find(ship_id=ship_id)

        assert result == []

    def test_sanctions_blacklisted(self, repository, factory):
        imo_id = 1234567

        ship = factory.create_ship(imo_id=imo_id)
        sanction = factory.create_ship_sanction(
            ship_id=ship.id,
            code=1,
            sanction_list_name='OFAC - WMD Supporters List',
        )
        blacklisted_sanction = factory.create_ship_sanction(
            ship_id=ship.id,
            code=2,
            sanction_list_name='World Bank List Other Sanctions',
        )
        blacklisted_sanction_list = factory.create_blacklisted_sanction_list(
            sanction_codes={
                blacklisted_sanction.code: {},
            },
        )

        result = repository.find(
            ship_id=ship.id,
            blacklisted_sanction_list_id=blacklisted_sanction_list.id,
        )

        assert len(result) == 1
        assert result[0].id == sanction.id
