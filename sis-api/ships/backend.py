"""Passes requests on to the installed backend(s) for processing"""
import logging
from ports.models import Country
from ships.backends.ihs_cached import CacheBackend

log = logging.getLogger(__name__)


class Broker(object):
    """Handles the interaction between the installed backends"""
    backend = CacheBackend()

    @staticmethod
    def ensure_codes(ship):
        """Ensure that ships are provided an ISO code for the flag country."""
        country_code = ship.get('flag_code')
        country_name = ship.get('flag_name')
        if not country_code and country_name:
            try:
                country_code = Country.lookup(name=country_name)
                ship['flag_code'] = country_code.code
            except (Country.DoesNotExist, AttributeError):
                log.debug("Couldn't find ISO code for flag country %s",
                          country_name)
        return ship

    def get_ship_by_imo(self, imo_id):
        """Get ship data using the IMO ID.
        :return: dict or None if no data is found
        """
        ship = self.backend.get_ship_by_imo(imo_id)
        if not ship:
            return None
        return self.ensure_codes(ship)

    def get_ship_by_mmsi(self, mmsi):
        """Get ship data using the MMSI.
        :return: dict or None if no data is found.
        """
        ship = self.backend.get_ship_by_mmsi(mmsi)
        if not ship:
            return None
        return self.ensure_codes(ship)

    def list_updated_ships(self, updated_since, imo_ids):
        """Get ship data using a list of IMO IDs, if those ships
        have been updated since the given date.
        :return: list of dicts with the updated ship info
        """
        result = {}
        data = self.backend.list_updated_ships(updated_since, imo_ids)
        for ship in data:
            ship.update(result.get(ship['imo_id'], {}))
            result[ship['imo_id']] = ship
        result = result.values()
        return list(map(self.ensure_codes, result))

    def list_ships_by_name(self, name):
        """Get ship data for ships with a certain name.
        :return: list of dicts
        """
        result = {}
        data = self.backend.list_ships_by_name(name)
        for ship in data:
            ship.update(result.get(ship['imo_id'], {}))
            result[ship['imo_id']] = ship

        log.info('Got ships by name: %s', list(result.keys()))
        result = result.values()
        return list(map(self.ensure_codes, result))
