from typing import Any

from screening_workers.lib.api.clients import Client
from screening_workers.lib.exceptions import ClientError


class SMHClient(Client):
    def __init__(self, base_uri, user, password):
        super(SMHClient, self).__init__(base_uri)
        self.base_uri = base_uri
        self.set_basic_auth(user, password)

    def get_smh(self, imo: str, **options: Any):
        """
        Get SMH data by IMO.

        Args:
            imo (str): The IMO number of the ship to be queried for.
            options (Any): Additional parameters

        Returns:
            object holding the response from SMH service.
        """
        try:
            url = f'{self.base_uri}/shipmovementhistory/{imo}'
            params = {}
            params.update(options)
            response = self.fetch(url, params=params)
        except Exception as exc:
            raise ClientError(exc)

        response.raise_for_status()
        return response.json()

    def get_port_data(self, **options: Any):
        """
        Get port data for given field/value set.

        Args:
            options (Any): Additional parameters (field=X and value=Y)

        Returns:
            object holding the response from SMH service.
        """
        try:
            url = f'{self.base_uri}/portdata/'
            params = {}
            params.update(options)
            response = self.fetch(url, params=params)
        except Exception as exc:
            raise ClientError(exc)

        response.raise_for_status()
        return response.json()

    def system_status(self):
        """
        Get SMH Service system status.

        Returns:
            api_clients.base_client.ResponseDict: Dictionary-like object
            holding the response from SMH service
        """
        url = f'{self.base_uri}/system/status'
        response = self.fetch(url)
        return response.json()
