import json

from django.test import TestCase
from tastypie.test import ResourceTestCaseMixin

from ships.tests.utils import serialize_datetime
from ships.tests.factories import CompanyHistoryFactory, UserFactory


class TestCompanyHistory(ResourceTestCaseMixin, TestCase):

    def get_credentials(self):
        pass

    def setUp(self):
        self.maxDiff = None

        self.user = UserFactory.create()
        self.client.login(username=self.user.username, password='letmein')

    def test_get_company_history(self):

        filter_imo = '12345'
        ch_record1 = CompanyHistoryFactory.create(
            imo_id=filter_imo,
            ignore=False,
        )
        ch_record2 = CompanyHistoryFactory.create(
            imo_id=filter_imo,
            ignore=False,
        )
        ch_record3 = CompanyHistoryFactory.create(
            imo_id='756836',
            ignore=False,
        )

        params = {'imo_id': filter_imo, 'order_by': 'effective_date'}
        response = self.client.get(
            '/api/v1/company_history',
            data=params,
            format='json',
        )

        self.assertEqual(response.status_code, 200)

        expected = {
            'meta': {'limit': 20, 'next': None, 'offset': 0, 'previous': None, 'total_count': 2},
            'objects': [
                {
                    'association_type': ch_record1.association_type,
                    'company_code': ch_record1.company_code,
                    'company_control_country': ch_record1.company_control_country,
                    'company_domicile_code': ch_record1.company_domicile_code,
                    'company_domicile_country': ch_record1.company_domicile_country,
                    'company_name': ch_record1.company_name,
                    'company_registration_country': ch_record1.company_registration_country,
                    'ignore': False,
                    'imo_id': ch_record1.imo_id,
                    'resource_uri': '/api/v1/company_history/1',
                    'timestamp': serialize_datetime(ch_record1.timestamp),
                    'effective_date': serialize_datetime(ch_record1.effective_date),
                },
                {
                    'association_type': ch_record2.association_type,
                    'company_code': ch_record2.company_code,
                    'company_control_country': ch_record2.company_control_country,
                    'company_domicile_code': ch_record2.company_domicile_code,
                    'company_domicile_country': ch_record2.company_domicile_country,
                    'company_name': ch_record2.company_name,
                    'company_registration_country': ch_record2.company_registration_country,
                    'ignore': False,
                    'imo_id': ch_record2.imo_id,
                    'resource_uri': '/api/v1/company_history/2',
                    'timestamp': serialize_datetime(ch_record2.timestamp),
                    'effective_date': serialize_datetime(ch_record2.effective_date),
                },
            ]
        }

        content = json.loads(response.content)
        self.assertEqual(content, expected)

    def test_get_company_history_ignore_filter(self):

        filter_imo = '123456'

        ch_record1 = CompanyHistoryFactory.create(imo_id=filter_imo, ignore=True)
        ch_record2 = CompanyHistoryFactory.create(imo_id=filter_imo, ignore=False)
        ch_record3 = CompanyHistoryFactory.create(imo_id='1111122')

        params = {"imo_id": filter_imo, "ignore": False}
        response = self.client.get('/api/v1/company_history', data=params, format='json')

        result = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(result['meta']['total_count'], 1)
        self.assertEqual(len(result['objects']), 1)

    def test_delete_company_history(self):
        filter_imo = '123456'
        data = {"imo_id": filter_imo}
        response = self.client.delete('/api/v1/company_history', data=data)
        self.assertHttpMethodNotAllowed(response)

    def test_post_company_history(self):
        filter_imo = '123456'
        data = {"imo_id": filter_imo}
        response = self.client.post(
            '/api/v1/company_history',
            data=data,
            content_type='application/json',
        )
        self.assertHttpMethodNotAllowed(response)

    def test_put_company_history(self):
        filter_imo = '123456'
        data = {"imo_id": filter_imo}
        response = self.client.put('/api/v1/company_history', data=data)
        self.assertHttpMethodNotAllowed(response)
