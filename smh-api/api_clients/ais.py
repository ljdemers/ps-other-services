import datetime
from typing import Dict, Optional

from api_clients.base_client import ApiClient, \
    BasicAuthMixin, ResponseDict
from api_clients.utils import json_logger
from ps_env_config import config


logger = json_logger(__name__, level=config.get('LOG_LEVEL'), sort_keys=False)


class AISClient(BasicAuthMixin, ApiClient):
    ssl_verify = False

    def get_ship_by_imo(self, imo: str) -> ResponseDict:
        """
        Get ship by IMO.

        Args:
            imo (str): The IMO number of the ship to be queried for.

        Returns:
            api_clients.base_client.ResponseDict: Dictionary-like
                object holding the response from AIS service with a list of
                results of ships for the given IMO number.
        """
        url = '/ship'
        params = {'q': f'imo_number:{imo}'}
        response_obj = self.get(url, params=params)

        def get_item(x):
            return x.get('position_timestamp', '0')

        # if multiple entries for the same IMO are retrieved,
        # pick the latest not null position timestamp
        data = response_obj.get('data', [])
        if len(data) > 1:
            sorted_list = sorted(data, key=get_item, reverse=True)
            response_obj['data'] = [sorted_list[0]]
            response_obj['count'] = 1

        return response_obj

    def get_track(
        self,
        mmsi: str,
        limit: int = 500,
        end_date: datetime.datetime = None,
        downsample_frequency_seconds: int or None = None
    ) -> ResponseDict:
        """
        Given MMSI number, gets the positions track of the ship.

        Args:
            mmsi (str): The MMSI number of the ship.
            limit (int): Limit of positions to be fetched.
            end_date (datetime.datetime): The last timestamp for which we want
                to get positions tracking data.
            downsample_frequency_seconds (int): down sampling frequency to use in AISAPI,
                0 or None to ignore

        Returns:
            api_clients.base_client.ResponseDict: Dictionary-like object
                holding the response from AIS service with a list of
                results of ship positions for the given MMSI number.
        """
        params = {
            'position_count': limit,
        }
        # make it backward compatible
        if downsample_frequency_seconds:
            params['downsample_frequency_seconds'] = downsample_frequency_seconds
        if end_date is not None:
            params['end_date'] = (  # type: ignore
                end_date.strftime('%Y-%m-%dT%H:%M:%S'))

        url = f'/track/{mmsi}'
        return self.get(url=url, params=params)

    def get_track_latest(self, mmsi: str) -> Dict:
        """
        Get latest position from track, alternative to ``get_status`` to
        retrieve ``source``.

        Args:
            mmsi (str): The MMSI number of the ship.

        Returns:
            api_clients.base_client.ResponseDict: Dictionary-like object
                holding the response from AIS service with a list of
                only 1 result of the latest known ship position for the
                given MMSI number.
        """
        params = {'position_count': 1}

        url = f'/track/{mmsi}'
        return self.get(url=url, params=params)

    def get_mmsi_from_imo(self, imo: str) -> Optional[str]:
        """
        Get MMSI from IMO number.

        Args:
            imo (str): The IMO number of the ship to be queried for.

        Returns:
            str: The MMSI number.
        """
        res = self.get_ship_by_imo(imo=imo)
        if res.error:
            return None

        try:
            return res['data'][0]['mmsi']
        except (ValueError, KeyError):
            return None

    def get_status(self, mmsi: str) -> ResponseDict:
        """
        Get status of the ship, given its MMSI number.

        Args:
            mmsi (str): The MMSI number of the ship.

        Returns:
            api_clients.base_client.ResponseDict: Dictionary-like object
                holding the response from AIS service with a map of
                ship/vessel data for the given MMSI number.
        """
        url = f'/ship/{mmsi}'
        return self.get(url)

    def get_static_and_voyage(self, mmsi: str) -> ResponseDict:
        """
        Get static and voyage data, given its MMSI number.

        Args:
            mmsi (str): The MMSI number of the ship.

        Returns:
            api_clients.base_client.ResponseDict: Dictionary-like object
                holding the response from AIS service with a map of
                ship/vessel data for the given MMSI number.
        """
        url = f'/static_and_voyage/{mmsi}'
        return self.get(url)

    def list_ships(self, params: Dict) -> ResponseDict:
        """
        List ships tracked by AIS Service.

        Args:
            params (dict): dictionary of params for the ``GET`` HTTP query.

        Returns:
            api_clients.base_client.ResponseDict: Dictionary-like object
                holding the response from AIS service with a list of results.
        """
        url = '/ship'
        if 'limit' not in params or int(params['limit']) > 19:
            params['limit'] = 20
        return self.get(url, params=params)

    def system_status(self) -> ResponseDict:
        """
        Get AIS Service system status.

        Returns:
            api_clients.base_client.ResponseDict: Dictionary-like object
                holding the response from AIS service with a list of results.
        """
        url = '/system/status'
        return self.get(url)
