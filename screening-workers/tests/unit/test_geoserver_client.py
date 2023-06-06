import pytest
from unittest import mock
from screening_workers.lib.geoserver_api.geoserver_client import \
    GeoServiceClient


class TestGeoServerClient:
    """ Unit Tests for GeoServer client """

    @pytest.fixture
    def client(self):
        """Returns a GoeServer client"""
        return GeoServiceClient("test")

    def test_in_zone(self, client):
        result = {'type': 'FeatureCollection',
                  'features':
                      [{'type': 'Feature',
                        'id': 'check_zone.fid--7ebcf699_161284a18d9_-7adc',
                        'properties':
                            {'name': 'Iran OFAC buffer zone',
                             'zone_name': 'Iran OFAC buffer zone',
                             'zone_type': 'POLYGON',
                             'zone_info': 'buffer',
                             'bbox': [-1, -1, 0, 0],
                             'area_id': 3, 'id': 6,
                             'layer_name': 'buffer'},
                        'geometry': None},
                       {'type': 'Feature',
                        'id': 'check_zone.fid--7ebcf699_161218d9_-7adb',
                        'properties': {'name': 'Iran OFAC zone',
                                       'zone_name': 'Iran OFAC zone',
                                       'zone_type': 'POLYGON',
                                       'zone_info': 'sanction',
                                       'bbox': [-1, -1, 0, 0],
                                       'area_id': 4, 'id': 7,
                                       'layer_name': 'sanction'},
                        'geometry': None}]}
        client.get = mock.Mock(return_value=result)
        expected = sorted([
            {
                'name': u'Iran OFAC buffer zone',
                'type': 'IN_BUFFER_ZONE'
            }, {
                'name': u'Iran OFAC zone',
                'type': 'IN_SANCTION_ZONE'
            }
        ], key=lambda x: x['name'])
        latitude = 29.4
        longitude = 59.5

        actual = sorted(
            client.in_zone(latitude, longitude),
            key=lambda x: x['name']
        )

        assert len(actual) == 2
        assert expected[0] == actual[0]
        assert expected[1] == actual[1]

    def test_get_sanctions_code(self, client):
        result = \
            {
                "features":
                [
                    {
                        "properties":
                        {
                            "zone_info": "sanction",
                            "metadata": "{\"flags\": [{\"code\": \"CUB\"}]}"
                        }
                    },
                    {
                        "properties":
                        {
                            "zone_info": "sanction",
                            "metadata": "{\"flags\": [{\"code\": \"SYR\"}]}"
                        }
                    }
                ]
            }

        expected = ['CUB', 'SYR']
        client.get = mock.Mock(return_value=result)
        actual = client.get_sanctioned_codes()

        assert len(actual) == 2
        assert expected[0] == actual[0]
        assert expected[1] == actual[1]

        assert client.is_code_in_sanctions('CUB') is True
        assert client.is_code_in_sanctions('USA') is False
