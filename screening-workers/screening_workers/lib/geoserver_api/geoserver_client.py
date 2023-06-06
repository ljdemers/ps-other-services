import copy
import urllib
import requests
import json
from screening_workers.lib.utils import json_logger

from screening_workers.lib.geoserver_api.exceptions import (
    GeoServerResponseError, GeoServerResponseDecodeError,
    UnknownGeoServerError,
)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls) \
                .__call__(*args, **kwargs)
        return cls._instances[cls]


class GeoServiceClient(object):
    """
    GeoServer client.
    cloned from PurpleTrac
    """

    __metaclass__ = Singleton

    IN_SANCTION_ZONE = "IN_SANCTION_ZONE"
    IN_WAR_ZONE = "IN_WAR_ZONE"
    IN_BUFFER_ZONE = "IN_BUFFER_ZONE"
    IN_COAST_ZONE = "IN_COAST_ZONE"

    PURPLETRAC_OWS = "purpletrac/ows"
    GEOFENCER_OWS = "geofencer/ows"
    CAS_OWS = "industry_zones/ows"
    CYCLONE_OWS = 'weather/ows'

    DEFAULT_ZONES = ['sanction', 'warzone', 'buffer']
    DEFAULT_ZONE_TYPES = {
        'sanction': IN_SANCTION_ZONE,
        'warzone': IN_WAR_ZONE,
        'buffer': IN_BUFFER_ZONE,
        'coast': IN_COAST_ZONE
    }
    DEFAULT_TYPENAME = 'purpletrac:check_zone'

    BASE_PARAMS = {
        'service': 'WFS',
        'version': '1.0.0',
        'request': 'GetFeature',
        'maxFeatures': '200',
        'outputFormat': 'json',
    }

    def __init__(self, base_url, timeout=60, log_level='INFO'):
        self.base_url = base_url
        self.logger = json_logger(__name__, level=log_level)
        self.timeout = timeout
        self.SANCTIONS_URL = self.get_wfs_url({
            'typeName': 'purpletrac:sanction_zones'})
        self.WARZONE_URL = self.get_wfs_url({
            'typeName': 'purpletrac:war_zones'})

    def get(self, url, params=None):
        """
        Retrieve geoserver data from the server.
        :param url: The URL to retrieve
         :type url: str
         :type params: dict
        :return: a dictionary containing the result or error
        """
        self.logger.debug("get(url=%s, params=%s)" % (url, params))
        resp = requests.get(url, params=params, timeout=self.timeout)

        try:
            resp.raise_for_status()
        except requests.exceptions.RequestException as err:
            raise GeoServerResponseError(str(err))
        except Exception as err:
            raise UnknownGeoServerError(str(err))

        try:
            return resp.json()
        except ValueError as err:
            raise GeoServerResponseDecodeError(str(err))
        except Exception as err:
            raise UnknownGeoServerError(str(err))

    def get_wfs(self, requested_params):
        """Return decoded WFS data.

            geoserver = GeoServer(settings.BASE_URL)
            features = geoserver.get_wfs({'typeName': 'purpletrac:war_zones'})

            :type requested_params: dict
        """
        assert 'typeName' in requested_params, "No 'typeName' in params!"
        params = copy.deepcopy(self.BASE_PARAMS)
        params.update(requested_params)
        return self.get(self.base_url + "wfs", params=params)

    def get_wfs_url(self, requested_params):
        assert 'typeName' in requested_params, "No 'typeName' in params!"
        params = copy.deepcopy(self.BASE_PARAMS)
        params.update(requested_params)
        return self.base_url + "wfs?" + urllib.parse.urlencode(params)

    @staticmethod
    def get_viewparams(lat, lon):
        return 'latitude:%.7f;longitude:%.7f' % (lat, lon)

    def in_zone(self, lat, lon,
                zones=DEFAULT_ZONES,
                in_zone_url=PURPLETRAC_OWS,
                zone_types=DEFAULT_ZONE_TYPES,
                type_name=DEFAULT_TYPENAME,
                requested_params=None
                ):
        """
        Get a list of zones containing a point from a Geoserver layer
        :param lat: latitude in degrees
         :type lat: float
        :param lon: longitude in degrees
         :type lon: float
        :param zones: zone types to locate
         :type zones: list
        :param in_zone_url: URL of the OWS
         :type in_zone_url: str
        :param zone_types: zones
         :type zone_types: dict
        :param type_name: name of the layer (`aaa:bbb`)
         :type type_name: str
        :param requested_params: request parameters
         :type requested_params: kwargs
        :return: a list of dicts
        """
        data = []
        in_zone_url = self.base_url + in_zone_url

        params = copy.deepcopy(self.BASE_PARAMS)
        params.update({
            'viewparams': self.get_viewparams(lat, lon),
            'typeName': type_name
        })
        if requested_params:
            params.update(requested_params)

        result = self.get(in_zone_url, params=params)
        for feature in result["features"]:

            if type_name == self.DEFAULT_TYPENAME:
                zone_info = feature["properties"]["layer_name"].strip()
                if (zone_info in zones) and (zone_info in zone_types):
                    data.append({
                        "type": zone_types[zone_info],
                        "name": feature["properties"]["name"].strip()
                    })
            else:
                zone_type = zone_types.keys()[0]
                feature['properties']['area_type'] = ''
                data.append({
                    'id': "{0}.{1}".format(
                        zone_type, feature["properties"]["id"]),
                    'properties': feature["properties"]
                })

        return data

    def in_geofencer(self, position, zones=None):
        url = self.base_url + self.GEOFENCER_OWS
        if zones is None:
            zones = 'warzone|sanction|ports'
        elif isinstance(zones, (list, tuple)):
            zones = '|'.join(zones)
        params = {
            'typeName': 'geofencer:geofencer',
            'viewparams': 'latitude:%s;longitude:%s;layer_names:%s' % (
                position.latitude, position.longitude, zones)
        }
        params.update(self.BASE_PARAMS)
        return self.get(url, params)

    def get_sanction_zones(self):
        return self.get(self.SANCTIONS_URL)

    def get_war_zones(self):
        return self.get(self.WARZONE_URL)

    def get_active_cyclones(self):
        if self.base_url.endswith('/'):
            url = '{0}{1}'.format(self.base_url, self.CYCLONE_OWS)
        else:
            url = '{0}/{1}'.format(self.base_url, self.CYCLONE_OWS)

        params = {
            'typeName': 'weather:cyclones',
        }
        params.update(self.BASE_PARAMS)

        return self.get(url, params)

    def get_sanctioned_codes(self):
        """ Call geoserver and get sanction zones.
        :returns: list flag/country codes of sanctioned countries
        :rtype: list
        """
        codes = []
        features = self.get_sanction_zones()['features']
        for feature in features:
            metadata = json.loads(feature['properties']['metadata'])
            for sanctioned_flag in metadata['flags']:
                codes.append(sanctioned_flag['code'].upper())

        return codes

    def get_war_zone_names(self):
        """ Call geoserver and get war zones.
        :returns: list flag/country codes of war zone countries
        :rtype: list
        """
        names = []
        features = self.get_war_zones()['features']
        for feature in features:
            zone = feature['properties']['zone_name']
            names.append(zone)

        return names

    def get_sanction_zones_list(self):
        """ Call geoserver and get sanction zones. """
        zones = {}
        for feature in self.get_sanction_zones()['features']:
            zones[feature['properties']['zone_name']] = \
                json.dumps(feature["geometry"])

        return zones

    def is_code_in_sanctions(self, flag_code):
        """ Check if flag/country code is in sanctioned country flags.
        :param flag_code: 3 character flag code
        :type flag_code: str, unicode
        :returns: True if flag code is in sanctions otherwise False
        :rtype: bool
        """
        codes = self.get_sanctioned_codes()
        if flag_code.upper() in codes:
            return True

        return False
