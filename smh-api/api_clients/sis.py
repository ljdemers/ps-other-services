from typing import Any, Dict, Optional, Tuple

from api_clients.base_client import ApiClient, ApiKeyAuthMixin, \
    ResponseDict


class SisClient(ApiKeyAuthMixin, ApiClient):

    @classmethod
    def get_authentication_names(cls) -> Tuple:
        return 'username', 'api_key'

    def get_ship_by_imo(self, imo: str) -> ResponseDict:
        url = f'/ships/{imo}'
        return self.get(url)

    def list_ship_inspections_by_imo(
        self, imo: str, limit: int = 100, offset: int = 0, **filters: Any
    ) -> ResponseDict:
        url = f'/ships/{imo}/inspections'
        params = {'limit': limit, 'offset': offset}
        params.update(filters)
        return self.get(url, params=params)

    def search_ships(
        self, params: Dict, limit: int = 20, offset: int = 0
    ) -> ResponseDict:
        url = f'/ship'
        params.update({'limit': limit, 'offset': offset})
        return self.get(url, params=params)

    def get_ship_type(
        self,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict] = None
    ) -> ResponseDict:
        filters = filters or {}
        url = f'/shiptype'
        params = {**{'limit': limit, 'offset': offset}, **filters}
        return self.get(url, params=params)

    def list_ship_movement_history_by_imo(
        self, imo: str, limit: int = 100, offset: int = 0, **filters: Any
    ) -> ResponseDict:
        url = f'/ship_movement'
        params = {'limit': limit, 'offset': offset, 'imo_id': imo}
        params.update(filters)
        return self.get(url, params=params)

    def system_status(self) -> ResponseDict:
        url = '/system/status'
        return self.get(url)

    def list_ships_by_name(
        self, name: str, limit: int = 100, offset: int = 0, **filters: Any
    ) -> ResponseDict:
        url = '/ships'
        params = {"limit": limit, "ship_name": name, "offset": offset}
        params.update(filters)
        return self.get(url, params=params)

    def list_mmsi_history(
        self, imo_number: str, **filters: Any
    ) -> ResponseDict:
        url = '/mmsi_history'
        params = {
            'imo_number': imo_number,
        }
        params.update(filters)
        return self.get(url, params=params)
