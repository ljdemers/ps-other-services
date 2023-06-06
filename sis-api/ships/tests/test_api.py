import datetime
import ujson

from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Q
from django.test.testcases import TestCase
from django.utils.timezone import make_naive
from freezegun import freeze_time
from tastypie.test import ResourceTestCaseMixin
from ships import models
from ships.models import ShipData
from ships.tests.factories import ShipDataFactory


class TestShipsApi(ResourceTestCaseMixin, TestCase):
    maxDiff = None

    emptyResultList = {'meta': {'offset': 0, 'total_count': 0, 'limit': 20,
                                'previous': None, 'next': None, },
                       'objects': []}

    firstObject = {
        "imo_id": "1234567", "mmsi": "123456789",
        "ship_name": "SS ONE",
        'flag_name': 'Denmark', "flag": None,
        'flag_code': 'DNK', "image": None,
        "thumbnail": None,
        "resource_uri": "/api/v1/ships/1234567",
    }
    secondObject = {
        "imo_id": "7654321", "mmsi": None,
        "ship_name": "SS TWO", "image": None,
        "flag": None, "thumbnail": None,
        "resource_uri": "/api/v1/ships/7654321",
    }
    thirdObject = {
        "imo_id": "2234567", "mmsi": "223456789",
        "ship_name": "NEW THREE",
        'flag_name': 'Denmark', 'flag_code': 'DNK',
        "image": None,
        "flag": {"code": "DNK", "name": "Denmark", "iso_3166_1_alpha_2": "DK",
                 "alt_name": "Denmark (Dis)"},
        "thumbnail": None,
        "resource_uri": "/api/v1/ships/2234567",
    }

    firstObjectFull = firstObject.copy()
    secondObjectFull = secondObject.copy()
    thirdObjectFull = thirdObject.copy()

    @staticmethod
    def serializeDatetime(d):
        if d is None:
            return

        if d.tzinfo is not None and d.tzinfo.utcoffset(d) is not None:
            d = make_naive(d)

        return d.isoformat()

    def setUp(self):
        super(TestShipsApi, self).setUp()
        self.user = User.objects.create_user(username='test_user',
                                             password='test')
        self.client.login(username='test_user', password='test')

        self.flag_1 = models.Flag.objects.get_or_create(
            code="DNK", name="Denmark", iso_3166_1_alpha_2="DK",
            alt_name="Denmark (Dis)",
            world_continent="Europe", world_region="Northern Europe")[0]

        self.flag_2 = models.Flag.objects.get_or_create(
            code="IRN", name="Iran", iso_3166_1_alpha_2="IR",
            world_continent="Asia",
            world_region="Southern Asia")[0]

        ship_data_1 = {
            "imo_id": "1234567", "attr1": "value1",
            "attr2": "value2",
            "mmsi": "123456789", "ship_name": "SS ONE",
            "flag_name": "Denmark",
            "flag_code": "DNK",
        }
        models.ShipData.objects.create(
            imo_id='1234567', mmsi="123456789", ship_name="SS ONE",
            flag_name='Denmark', shiptype_level_5="Nuclear Submarine",
            data=ship_data_1)

        models.ShipData.objects.create(
            imo_id='7654321', ship_name="SS TWO",
            data={"imo_id": "7654321", "attr1": "value3", "attr2": "value4",
                  "ship_name": "SS TWO"})

        self.dnk_ = {"imo_id": "2234567", "attr1": "value1", "attr2": "value2",
                     "mmsi": "223456789", "ship_name": "NEW THREE",
                     "flag_name": "Denmark", "flag_code": "DNK", }
        ship_data_2 = self.dnk_
        self.create = models.ShipData.objects.create(
            imo_id='2234567', mmsi="223456789", ship_name="NEW THREE",
            flag_name='Denmark', shiptype_level_5="Backhoe Dredger",
            flag=self.flag_1, data=ship_data_2)

        ship_data_3 = {
            "imo_id": "3234567", "attr1": "value1",
            "attr2": "value2",
            "mmsi": "223456781", "ship_name": "NEW FOUR",
            "flag_name": "Iran",
            "flag_code": "IRN",
        }
        self.ship_3 = models.ShipData.objects.create(
            imo_id='3234567', mmsi="223456781", ship_name="NEW FOUR",
            flag_name='Iran', shiptype_level_5="Alcohol Tanker",
            flag=self.flag_2, data=ship_data_3)

        models.ShipImage.objects.create(
            ship_data=self.ship_3, imo_id="3234567", url="big_image.jpg",
            width=500, height=500, filename="big_image.jpg")
        models.ShipImage.objects.create(
            ship_data=self.ship_3, imo_id="3234567", url="small_image.jpg",
            width=50, height=50, filename="small_image.jpg")

        self.firstObjectFull.update({'attr1': 'value1', 'attr2': 'value2'})
        self.secondObjectFull.update({'attr1': 'value3', 'attr2': 'value4'})
        self.thirdObjectFull.update({'attr1': 'value1', 'attr2': 'value2'})

        self.mmsi_history_1 = models.MMSIHistory.objects.create(
            imo_number='3234567', mmsi="223456785",
            effective_to=datetime.datetime(2018, 1, 1),
        )
        self.mmsi_history_1.effective_from = datetime.datetime(2017, 1, 2)
        self.mmsi_history_1.save()
        self.mmsi_history_2 = models.MMSIHistory.objects.create(
            imo_number='3234567', mmsi="223456784",
            effective_to=datetime.datetime(2018, 6, 1),
        )
        self.mmsi_history_2.effective_from = datetime.datetime(2018, 1, 2)
        self.mmsi_history_2.save()
        self.mmsi_history_3 = models.MMSIHistory.objects.create(
            imo_number='3234567', mmsi="223456783",
            effective_to=datetime.datetime(2018, 9, 1),
        )
        self.mmsi_history_3.effective_from = datetime.datetime(2018, 6, 2)
        self.mmsi_history_3.save()
        self.mmsi_history_4 = models.MMSIHistory.objects.create(
            imo_number='3234567', mmsi="223456782",
            effective_to=datetime.datetime(2018, 12, 1),
        )
        self.mmsi_history_4.effective_from = datetime.datetime(2018, 9, 2)
        self.mmsi_history_4.save()
        self.mmsi_history_5 = models.MMSIHistory.objects.create(
            imo_number='3234567', mmsi="223456781",
        )
        self.mmsi_history_5.effective_from = datetime.datetime(2018, 12, 2)
        self.mmsi_history_5.save()

    def test_get_unauthenticated_list(self):
        self.client.logout()
        resp = self.client.get('/api/v1/ships', format='json')
        self.assertHttpUnauthorized(resp)

    def test_get_ships_no_params(self):
        resp = self.client.get('/api/v1/ships', format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result, self.emptyResultList)

    def test_get_ships_by_imo_id_not_found(self):
        resp = self.client.get('/api/v1/ships?imo_id=1111111', format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result, self.emptyResultList)

    def test_get_ships_by_imo_id(self):
        resp = self.client.get('/api/v1/ships?imo_id=1234567', format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result['meta']['total_count'], 1)
        self.assertEqual(len(result['objects']), 1)
        self.assertEqual(result['objects'][0], self.firstObjectFull)

    def test_get_ships_by_imo_id_with_flag(self):
        resp = self.client.get('/api/v1/ships?imo_id=2234567', format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result['meta']['total_count'], 1)
        self.assertEqual(len(result['objects']), 1)
        self.assertEqual(result['objects'][0], self.thirdObjectFull)

    def test_get_ships_by_imo_id_multi(self):
        resp = self.client.get('/api/v1/ships?imo_id=1234567&imo_id=7654321',
                               format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result['meta']['total_count'], 2)
        self.assertEqual(len(result['objects']), 2)
        self.assertEqual(result['objects'][0], self.firstObjectFull)
        self.assertEqual(result['objects'][1], self.secondObjectFull)

    def test_get_ships_by_imo_id__in(self):
        resp = self.client.get('/api/v1/ships?imo_id__in=1234567,7654321',
                               format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result['meta']['total_count'], 2)
        self.assertEqual(len(result['objects']), 2)
        self.assertEqual(result['objects'][0], self.firstObjectFull)
        self.assertEqual(result['objects'][1], self.secondObjectFull)

    def test_get_ships_by_mmsi_not_found(self):
        resp = self.client.get('/api/v1/ships?mmsi=111111111', format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result, self.emptyResultList)

    def test_get_ships_by_mmsi(self):
        resp = self.client.get('/api/v1/ships?mmsi=123456789', format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result['meta']['total_count'], 1)
        self.assertEqual(len(result['objects']), 1)
        self.assertEqual(result['objects'][0], self.firstObjectFull)

    def test_get_ships_by_mmsi_flag(self):
        resp = self.client.get('/api/v1/ships?mmsi=223456789', format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result['meta']['total_count'], 1)
        self.assertEqual(len(result['objects']), 1)
        self.assertEqual(result['objects'][0], self.thirdObjectFull)

    def test_get_ships_by_name_not_found(self):
        resp = self.client.get('/api/v1/ships?ship_name=XXXX', format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result, self.emptyResultList)

    def test_get_ships_by_name_empty(self):
        resp = self.client.get('/api/v1/ships?ship_name=', format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result, self.emptyResultList)

    def test_get_ships_by_name_single(self):
        resp = self.client.get('/api/v1/ships?ship_name=ONE', format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result['meta']['total_count'], 1)
        self.assertEqual(len(result['objects']), 1)
        self.assertEqual(result['objects'][0], self.firstObjectFull)

    def test_get_ships_by_name_single_flag(self):
        resp = self.client.get('/api/v1/ships?ship_name=THREE', format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result['meta']['total_count'], 1)
        self.assertEqual(len(result['objects']), 1)
        self.assertEqual(result['objects'][0], self.thirdObjectFull)

    def test_get_ships_by_name_multi(self):
        resp = self.client.get('/api/v1/ships?ship_name=SS', format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result['meta']['total_count'], 2)
        self.assertEqual(len(result['objects']), 2)
        self.assertTrue(self.firstObjectFull in result['objects'])
        self.assertTrue(self.secondObjectFull in result['objects'])

    def test_get_ships_by_name_many_terms(self):
        resp = self.client.get('/api/v1/ships?ship_name=ONE&ship_name=TWO',
                               format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result['meta']['total_count'], 2)
        self.assertEqual(len(result['objects']), 2)
        self.assertTrue(self.firstObjectFull in result['objects'])
        self.assertTrue(self.secondObjectFull in result['objects'])

    def test_get_ship_detail_unauthenticated(self):
        self.client.logout()
        resp = self.client.get('/api/v1/ships/1234567', format='json')
        self.assertHttpUnauthorized(resp)

    def test_get_ship_detail_not_found(self):
        resp = self.client.get('/api/v1/ships/1111111', format='json')
        self.assertHttpNotFound(resp)

    def test_get_ship_detail_found(self):
        resp = self.client.get('/api/v1/ships/1234567', format='json')
        self.assertHttpOK(resp)
        result = ujson.loads(resp.content)
        self.assertEqual(result, self.firstObjectFull)

    def test_get_ship_by_imo_id(self):
        resp = self.client.get('/api/v1/ship?imo_id=3234567', format='json')
        expected = {
            'meta': {
                'limit': 20, 'next': None, 'offset': 0, 'previous': None,
                'total_count': 1
            },
            'objects': [
                {
                    'call_sign': None,
                    'data': {"imo_id": "3234567", "attr1": "value1",
                             "attr2": "value2", "mmsi": "223456781",
                             "ship_name": "NEW FOUR", "flag_name": "Iran",
                             "flag_code": "IRN"},
                    'flag': {'alt_name': None, 'code': 'IRN',
                             'iso_3166_1_alpha_2': 'IR',
                             'name': 'Iran', 'resource_uri': '',
                             'world_continent': 'Asia',
                             'world_region': 'Southern Asia'},
                    'flag_name': 'Iran',
                    'gross_tonnage': None,
                    'group_beneficial_owner': None,
                    'id': self.ship_3.id,
                    'image': 'big_image.jpg',
                    'imo_id': '3234567',
                    'length_overall_loa': None,
                    'mmsi': '223456781',
                    'operator': None,
                    'original_data': '{}',
                    'port_of_registry': None,
                    'registered_owner': None,
                    'resource_uri': '/api/v1/ship/%s' % self.ship_3.id,
                    'ship_manager': None,
                    'ship_name': 'NEW FOUR',
                    'ship_status': None,
                    'shiptype_level_5': "Alcohol Tanker",
                    'technical_manager': None,
                    'thumbnail': 'small_image.jpg',
                    'year_of_build': None}]}
        self.assertHttpOK(resp)
        actual = resp.json()
        del actual["objects"][0]["updated"]
        self.assertDictEqual(actual, expected)

    def test_get_ship_from_china_by_imo_id(self):
        ship_data = {
            'flag_name': 'Panama', 'hull_type': 'Double Hull',
            'ship_status': 'In Service/Commission',
            'shipbuilder': 'Tsuji Heavy Industries Jiangsu',
            'gross_tonnage': '19999', 'year_of_build': '2013',
            'hull_type_code': 'DHE',
            'country_of_build': "China, People's Republic Of"}
        factoried_ship_data = ShipDataFactory.create(data=ship_data)
        resp = self.client.get('/api/v1/ship?imo_id={}'.format(
            factoried_ship_data.imo_id), format='json')
        self.assertHttpOK(resp)
        actual = resp.json()
        self.assertEqual(actual['objects'][0]['data'],
                         ship_data)

    def test_can_search_with_q_object_for_ship_name_and_imo(self):
        models.ShipData.objects.create(
            imo_id='7777777',
            ship_name="SS TWO",
            data='{"imo_id":"7654321","attr1":"value3","attr2":"value4",'
                 '"ship_name":"SS TWO"}',
        )
        models.ShipData.objects.create(
            imo_id='7777778',
            ship_name="7777777",
            data='{"imo_id":"7654321","attr1":"value3","attr2":"value4",'
                 '"ship_name":"SS TWO"}',
        )
        data = {
            'q': '7654',
        }
        resp = self.client.get('/api/v1/ship/', data=data, format='json')
        payload = ujson.loads(resp.content)
        expected = models.ShipData.objects.filter(
            Q(ship_name__istartswith=data['q']) | Q(
                imo_id__istartswith=data['q'])
        )
        self.assertEqual(
            set([x['id'] for x in payload['objects']]),
            set([x.pk for x in expected])
        )

    def test_shiptype_resource(self):
        params = {
            'shiptype_level_5__istartswith': 'Alc',
            'format': 'json',
        }
        resp = self.client.get('/api/v1/shiptype', data=params)
        self.assertValidJSONResponse(resp)
        expected = {
            'meta': {'limit': 20,
                     'next': None,
                     'offset': 0,
                     'previous': None,
                     'total_count': 1},
            'objects': [
                {'shiptype_level_5': 'Alcohol Tanker'},
            ]
        }

        actual = ujson.loads(resp.content)
        self.assertDictEqual(expected, actual)

    def test_imo_resource(self):
        response = self.client.get(
            reverse(
                'api_dispatch_list',
                kwargs={'resource_name': 'imos', 'api_name': 'v1'}
            )
        )
        self.assertValidJSONResponse(response)

        total_ships = ShipData.objects.all().order_by('imo_id')

        expected = {
            u'meta': {u'limit': 10000,
                      u'next': None,
                      u'offset': 0,
                      u'previous': None,
                      u'total_count': total_ships.count()},
            u'objects': [
                {u'imo_id': str(ship.imo_id)} for ship in total_ships
            ]
        }

        actual = ujson.loads(response.content)
        self.assertDictEqual(expected, actual)

    @freeze_time('2019-02-11 9:15:00.723488')
    def test_imo_history_effective_delta(self):
        params = {
            'imo_number': '3234567',
            'effective_delta': 'year',
            'format': 'json',
        }
        response = self.client.get(
            reverse(
                'api_dispatch_list',
                kwargs={'resource_name': 'mmsi_history', 'api_name': 'v1'}
            ),
            data=params,
        )
        self.assertValidJSONResponse(response)

        expected = {
            'meta': {
                'limit': 20,
                'next': None,
                'offset': 0,
                'previous': None,
                'total_count': 4,
            },
            'objects': [
                {
                    'created': self.serializeDatetime(history.created),
                    'modified': self.serializeDatetime(history.modified),
                    'effective_from': self.serializeDatetime(
                        history.effective_from),
                    'effective_to': self.serializeDatetime(
                        history.effective_to),
                    'id': history.id,
                    'imo_number': '3234567',
                    'mmsi': history.mmsi,
                    'resource_uri': '/api/v1/mmsi_history/%s' % history.id,
                }
                for history in [
                    self.mmsi_history_2,
                    self.mmsi_history_3,
                    self.mmsi_history_4,
                    self.mmsi_history_5,
                ]
            ],
        }

        actual = ujson.loads(response.content)
        self.assertDictEqual(expected, actual)

    @freeze_time('2019-02-11 9:15:00.723488')
    def test_imo_history_effective_delta_desc(self):
        params = {
            'imo_number': '3234567',
            'effective_delta': 'year',
            'order_by': '-effective_from',
            'format': 'json',
        }
        response = self.client.get(
            reverse(
                'api_dispatch_list',
                kwargs={'resource_name': 'mmsi_history', 'api_name': 'v1'}
            ),
            data=params,
        )
        self.assertValidJSONResponse(response)

        expected = {
            'meta': {
                'limit': 20,
                'next': None,
                'offset': 0,
                'previous': None,
                'total_count': 4,
            },
            'objects': [
                {
                    'created': self.serializeDatetime(history.created),
                    'modified': self.serializeDatetime(history.modified),
                    'effective_from': self.serializeDatetime(
                        history.effective_from),
                    'effective_to': self.serializeDatetime(
                        history.effective_to),
                    'id': history.id,
                    'imo_number': '3234567',
                    'mmsi': history.mmsi,
                    'resource_uri': '/api/v1/mmsi_history/%s' % history.id,
                }
                for history in [
                    self.mmsi_history_5,
                    self.mmsi_history_4,
                    self.mmsi_history_3,
                    self.mmsi_history_2,
                ]
            ],
        }

        actual = ujson.loads(response.content)
        self.assertDictEqual(expected, actual)
