import datetime as dt
import json

from django.test import TestCase
from tastypie.test import ResourceTestCaseMixin

from ships.tests.utils import serialize_datetime
from ships.tests.factories import FlagHistoryFactory, UserFactory


class TestFlagHistory(ResourceTestCaseMixin, TestCase):
    def get_credentials(self):
        pass

    def setUp(self):
        self.maxDiff = None

        self.user = UserFactory.create()
        self.client.login(username=self.user.username, password='letmein')

    def test_get_flag_history(self):
        filter_imo = '123456'
        record1 = FlagHistoryFactory.create(
            imo_id=filter_imo, ignore=False
        )
        record2 = FlagHistoryFactory.create(
            imo_id=filter_imo, ignore=False
        )
        record3 = FlagHistoryFactory.create(
            imo_id='1111122', ignore=False
        )

        params = {'imo_id': filter_imo, 'order_by': 'timestamp'}
        response = self.client.get(
            '/api/v1/flag_history',
            data=params,
            format='json',
        )

        self.assertEqual(response.status_code, 200)

        expected = {
            'meta': {
                'limit': 20,
                'next': None,
                'offset': 0,
                'previous': None,
                'total_count': 2,
            },
            'objects': [
                {
                    'timestamp': serialize_datetime(record1.timestamp),
                    'flag': {
                        "alt_name": record1.flag.alt_name,
                        "code": record1.flag.code,
                        "iso_3166_1_alpha_2": record1.flag.iso_3166_1_alpha_2,
                        "name": record1.flag.name,
                        "resource_uri": "",
                        "world_continent": record1.flag.world_continent,
                        "world_region": record1.flag.world_region,
                    },
                    'imo_id': record1.imo_id,
                    'flag_name': record1.flag_name,
                    'flag_effective_date': serialize_datetime(record1.flag_effective_date),
                    'resource_uri': '/api/v1/flag_history/1',
                    'ignore': False,
                },
                {
                    'timestamp': serialize_datetime(record2.timestamp),
                    'flag': {
                        "alt_name": record2.flag.alt_name,
                        "code": record2.flag.code,
                        "iso_3166_1_alpha_2": record2.flag.iso_3166_1_alpha_2,
                        "name": record2.flag.name,
                        "resource_uri": "",
                        "world_continent": record2.flag.world_continent,
                        "world_region": record2.flag.world_region,
                    },
                    'imo_id': record2.imo_id,
                    'flag_name': record2.flag_name,
                    'flag_effective_date': serialize_datetime(record2.flag_effective_date),
                    'resource_uri': '/api/v1/flag_history/2',
                    'ignore': False,
                },
            ],
        }

        data = json.loads(response.content)
        self.assertEqual(data, expected)

    def test_get_flag_history_ignore_filter(self):
        filter_imo = '123456'
        record1 = FlagHistoryFactory.create(imo_id=filter_imo, ignore=True)
        record2 = FlagHistoryFactory.create(imo_id=filter_imo, ignore=False)
        record3 = FlagHistoryFactory.create(imo_id='1111122')

        params = {"imo_id": filter_imo, "ignore": False}
        response = self.client.get('/api/v1/flag_history', data=params, format='json')

        result = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result['meta']['total_count'], 1)
        self.assertEqual(len(result['objects']), 1)

    def test_delete_flag_history(self):
        filter_imo = '123456'
        data = {"imo_id": filter_imo}
        response = self.client.delete('/api/v1/flag_history', data=data)
        self.assertHttpMethodNotAllowed(response)

    def test_post_flag_history(self):
        filter_imo = '123456'
        data = {"imo_id": filter_imo}
        response = self.client.post('/api/v1/flag_history', data=data, content_type='application/json')
        self.assertHttpMethodNotAllowed(response)

    def test_put_flag_history(self):
        filter_imo = '123456'
        data = {"imo_id": filter_imo}
        response = self.client.put('/api/v1/flag_history', data=data)
        self.assertHttpMethodNotAllowed(response)
