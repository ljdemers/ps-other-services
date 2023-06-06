from requests.exceptions import HTTPError

from screening_workers.lib.utils import str2date
from screening_workers.lib.api.clients import Client
from screening_workers.lib.exceptions import ClientError


class AISClient(Client):
    def __init__(self, base_uri, user, password):
        super(AISClient, self).__init__(base_uri)
        self.set_basic_auth(user, password)

    def get_track(self, mmsi, end_date=None, position_count=None) -> dict:
        """ Given an MMSI number, queries the AIS Service to get track.
        Args:
            mmsi (str): The MMSI number. Must be a string with only digits.
            end_date: (`obj`:datetime.datetime, optional) A timezone aware
                ``datetime.datetime`` object.
            position_count (`obj`:int, optional) Number of positions to
                return
        Returns:
            (dict): The AIS data for the given MMSI ship:
                {
                    course: 128.3,
                    extdata: {
                        channel: "A",
                        msgtype: 1,
                        source: "rORBCOMM000"
                    },
                    heading: 123,
                    latitude: 27.804085,
                    longitude: 34.943848,
                    mmsi: 413305450,
                    speed: 4.2,
                    timestamp: "2017-07-17T09:39:06Z"
                }
        """
        try:
            data = {}
            if isinstance(position_count, int):
                data['position_count'] = position_count

            if end_date and isinstance(end_date, str):
                data['end_date'] = end_date

            response = self.fetch(
                '/api/v2/track/{mmsi}'.format(mmsi=mmsi),
                data,
            )

        except Exception as exc:
            raise ClientError(exc)

        response.raise_for_status()

        return response.json(), response.status_code

    def get_all_track(self, mmsi, stop_date=None, position_count=None) -> list:
        """ Get all positions for a given MMSI up to stop_date.
        Args:
            mmsi (str): 9 digit MMSI number.
            stop_date (`obj`:datetime.datetime, optional) A timezone aware
                ``datetime.datetime`` object.
            position_count (`obj`:int, optional): Number of positions to
                return.
        Returns:
            list: Of positions dictionaries.
        Raises:
            ClientError: When code doesn't execute as expected.
            NotFoundError: When MMSI is not found on AIS.
            RemoteServiceError: When the AIS returns a 500 status code.
        """
        starts_with = 'track returned no results for mmsi'
        track = []
        end_date = None
        while True:
            try:
                track_data, status_code = self.get_track(
                    mmsi=mmsi,
                    end_date=end_date,
                    position_count=position_count,
                )
            except HTTPError as exc:
                if exc.response.status_code == 404:
                    break
                raise

            if status_code == 404 or \
                    track_data.get('message', '').lower(). \
                    startswith(starts_with):
                # We've reached the end of the data stream so stop calling AIS.
                break

            track.extend(track_data.get('data', []))

            next_link = track_data.get('next_link')

            end_date_str = None
            try:
                end_date_str = next_link.split('=')[1]
                end_date = str2date(end_date_str)
            except Exception:
                pass

            if end_date_str is None:
                # There's no more data to consume. Stop processing it.
                break

            if stop_date and end_date <= stop_date:
                break

            end_date = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')

        return track
