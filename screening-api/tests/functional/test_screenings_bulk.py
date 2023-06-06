from io import BytesIO
from os import path
from unittest import mock
import json
import pytest

from freezegun import freeze_time

from screening_api.lib.messaging.publishers import CeleryTaskPublisher
from screening_api.screenings_bulk.enums import BulkScreeningStatus
from screening_api.screenings_bulk.subscribers import (
    BulkScreeningsValidationSubscriber,
)


class TestScreeningsBulkViewOptions:

    uri = '/v1/screenings/_bulk'

    def test_allowed_methods(self, test_client):
        env, resp = test_client.options(self.uri, as_tuple=True)

        assert resp.status_code == 200
        assert set(resp.allow) == set([
            'OPTIONS', 'GET', 'POST', 'HEAD', 'DELETE'])
        assert resp.headers['Access-Control-Allow-Origin'] == '*'


@pytest.mark.usefixtures('authenticated')
class TestScreeningsBulkViewGet:

    uri = '/v1/screenings/_bulk'

    def test_unauthenticated(self, test_client):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.get(self.uri, as_tuple=True)

        assert resp.status_code == 401

    @freeze_time("2001-09-11 07:59:00")
    def test_valid(self, test_client, factory):
        account_id = 54321
        bulk_screening_1 = factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.PENDING,
            result=None,
        )
        bulk_screening_2 = factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.DONE,
            result=False,
        )
        bulk_screening_3 = factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.DONE,
            result=True,
        )

        env, resp = test_client.get(self.uri, as_tuple=True)

        assert resp.status_code == 200
        url = "{0}://{1}{2}".format(
            env['wsgi.url_scheme'], env['HTTP_HOST'], env['PATH_INFO']
        )
        assert resp.json == {
            'data': [
                {
                    'account_id': account_id,
                    'created': '2001-09-11T07:59:00Z',
                    'id': bulk_screening_3.id,
                    'imo_id': bulk_screening_3.imo_id,
                    'status': 'DONE',
                    'result': True,
                    'updated': '2001-09-11T07:59:00Z',
                },
                {
                    'account_id': account_id,
                    'created': '2001-09-11T07:59:00Z',
                    'id': bulk_screening_2.id,
                    'imo_id': bulk_screening_2.imo_id,
                    'status': 'DONE',
                    'result': False,
                    'updated': '2001-09-11T07:59:00Z',
                },
                {
                    'account_id': account_id,
                    'created': '2001-09-11T07:59:00Z',
                    'id': bulk_screening_1.id,
                    'imo_id': bulk_screening_1.imo_id,
                    'status': 'PENDING',
                    'result': None,
                    'updated': '2001-09-11T07:59:00Z',
                },
            ],
            'links': {
                "first": url,
            },
            'meta': {
                'count': 3,
            }
        }

    @freeze_time("2001-09-11 07:59:00")
    def test_statuses_filter(self, test_client, factory):
        account_id = 54321
        factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.SCHEDULED,
            result=None,
        )
        bulk_screening_2 = factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.PENDING,
            result=None,
        )
        factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.DONE,
            result=True,
        )
        params = {'statuses': 'PENDING'}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        url = "{0}://{1}{2}?{3}".format(
            env['wsgi.url_scheme'], env['HTTP_HOST'], env['PATH_INFO'],
            env['QUERY_STRING'],
        )
        expected_list = [bulk_screening_2, ]
        expected_data = [
            {
                'account_id': account_id,
                'created': '2001-09-11T07:59:00Z',
                'id': bulk_screening.id,
                'imo_id': bulk_screening.imo_id,
                'status': 'PENDING',
                'result': None,
                'updated': '2001-09-11T07:59:00Z',
            } for bulk_screening in expected_list
        ]
        assert resp.json == {
            'data': expected_data,
            'meta': {
                'count': len(expected_list),
            },
            'links': {
                "first": url,
            },
        }

    @freeze_time("2001-09-11 07:59:00")
    def test_results_filter(self, test_client, factory):
        account_id = 54321
        factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.PENDING,
            result=None,
        )
        bulk_screening_2 = factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.DONE,
            result=False,
        )
        factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.DONE,
            result=True,
        )
        params = {'results': 'false'}

        env, resp = test_client.get(
            self.uri, query_string=params, as_tuple=True)

        assert resp.status_code == 200
        url = "{0}://{1}{2}?{3}".format(
            env['wsgi.url_scheme'], env['HTTP_HOST'], env['PATH_INFO'],
            env['QUERY_STRING'],
        )
        expected_list = [bulk_screening_2, ]
        expected_data = [
            {
                'account_id': account_id,
                'created': '2001-09-11T07:59:00Z',
                'id': bulk_screening.id,
                'imo_id': bulk_screening.imo_id,
                'status': 'DONE',
                'result': False,
                'updated': '2001-09-11T07:59:00Z',
            } for bulk_screening in expected_list
        ]
        assert resp.json == {
            'data': expected_data,
            'meta': {
                'count': len(expected_list),
            },
            'links': {
                "first": url,
            },
        }


@pytest.mark.usefixtures('authenticated')
class TestScreeningsBulkViewPost:

    uri = '/v1/screenings/_bulk'

    @pytest.fixture
    def data_file_reader(self):
        def read_file(filename):
            directory = path.abspath(path.dirname(__file__))
            path_full = path.join(directory, filename)
            with open(path_full, 'rb') as handler:
                return handler.read()
        return read_file

    @pytest.fixture
    def csv_file(self, data_file_reader):
        csv_filename = 'data/test.csv'
        return data_file_reader(csv_filename)

    @pytest.fixture
    def invalid_csv_file(self, data_file_reader):
        csv_filename = 'data/test_invalid.csv'
        return data_file_reader(csv_filename)

    @pytest.fixture
    def xls_file(self, data_file_reader):
        xls_filename = 'data/test.xls'
        return data_file_reader(xls_filename)

    def test_unauthenticated(self, test_client):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.post(self.uri, as_tuple=True)

        assert resp.status_code == 401

    @mock.patch('screening_api.lib.messaging.publishers.get_origin')
    @mock.patch('screening_api.lib.messaging.publishers.uuid')
    @mock.patch('kombu.messaging.Producer.publish')
    def test_valid_json(
            self, m_publish, m_uuid, m_get_origin, test_client,
            application):
        frozen_uuid = '12345678-1234-1234-1234-1234567890ab'
        frozen_origin = 'origin@host'
        m_publish.return_value = None
        m_uuid.return_value = frozen_uuid
        m_get_origin.return_value = frozen_origin
        account_id = 54321
        imo_ids = [12, 13, 14]
        data_json = {
            'imo_ids': imo_ids,
        }
        data = json.dumps(data_json)

        env, resp = test_client.post(
            self.uri, data=data,
            content_type='application/json', as_tuple=True,
        )

        assert resp.status_code == 202
        bulk_screenings = [
            application.bulk_screenings_repository.get(imo_id=imo_id)
            for imo_id in map(str, imo_ids)
        ]
        for bulk_screening in bulk_screenings:
            assert bulk_screening.account_id == account_id
        assert m_publish.call_count == len(imo_ids)
        calls = [
            mock.call(
                json.dumps(
                    [[bulk_screening.id], {}, None]
                ),
                content_encoding='utf-8', content_type='application/json',
                correlation_id=frozen_uuid,
                headers={
                    'id': frozen_uuid,
                    'lang': CeleryTaskPublisher.lang,
                    'task': BulkScreeningsValidationSubscriber.name,
                    'argsrepr': str((bulk_screening.id,)),
                    'kwargsrepr': str({}),
                    'origin': frozen_origin,
                }
            )
            for bulk_screening in bulk_screenings
        ]
        m_publish.assert_has_calls(calls, any_order=True)

    def test_valid_csv(self, test_client, csv_file):
        input_stream = BytesIO(csv_file)
        env, resp = test_client.post(
            self.uri, input_stream=input_stream,
            content_type='text/csv', as_tuple=True,
        )

        assert resp.status_code == 202

    def test_valid_csv_ms_excel(self, test_client, csv_file):
        input_stream = BytesIO(csv_file)
        env, resp = test_client.post(
            self.uri, input_stream=input_stream,
            content_type='application/vnd.ms-excel', as_tuple=True,
        )

        assert resp.status_code == 202

    def test_valid_form_csv(self, test_client, csv_file):
        datafile = (BytesIO(csv_file), 'testfile.csv')
        data = {
            'file': datafile,
        }
        env, resp = test_client.post(
            self.uri, data=data,
            content_type='multipart/form-data', as_tuple=True,
        )

        assert resp.status_code == 202

    def test_invalid_csv(self, test_client, invalid_csv_file):
        input_stream = BytesIO(invalid_csv_file)
        env, resp = test_client.post(
            self.uri, input_stream=input_stream,
            content_type='text/csv', as_tuple=True,
        )

        assert resp.status_code == 202

    def test_not_accepted_xml(self, test_client, xls_file):
        input_stream = BytesIO(xls_file)
        env, resp = test_client.post(
            self.uri, input_stream=input_stream,
            content_type='text/csv', as_tuple=True,
        )

        assert resp.status_code == 400

    def test_invalid_content_type(self, test_client):
        data = json.dumps({
            'imo_ids': [12, 13, 14],
        })
        env, resp = test_client.post(
            self.uri, data=data, content_type='text/html',
            as_tuple=True,
        )

        assert resp.status_code == 415

    def test_no_imo_ids(self, test_client):
        data = json.dumps({})
        env, resp = test_client.post(
            self.uri, data=data, content_type='application/json',
            as_tuple=True,
        )

        assert resp.status_code == 400

    def test_invalid_imo_ids(self, test_client):
        data = json.dumps({
            'imo_ids': ['two', 'three', 'four'],
        })
        env, resp = test_client.post(
            self.uri, data=data, content_type='application/json',
            as_tuple=True,
        )

        assert resp.status_code == 400


@pytest.mark.usefixtures('authenticated')
class TestScreeningsBulkViewDelete:

    uri = '/v1/screenings/_bulk'

    def test_unauthenticated(self, test_client):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.delete(self.uri, as_tuple=True)

        assert resp.status_code == 401

    def test_delete_non_existing(self, test_client):
        env, resp = test_client.delete(self.uri, as_tuple=True)

        assert resp.status_code == 204
        assert not resp.data

    def test_valid(self, test_client, factory, application):
        account_id = 54321
        account_id_2 = 54322
        bulk_screening_1 = factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.PENDING,
            result=None,
        )
        bulk_screening_2 = factory.create_bulk_screening(
            account_id=account_id_2, status=BulkScreeningStatus.DONE,
            result=False,
        )
        bulk_screening_3 = factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.DONE,
            result=True,
        )
        bulk_screenings = [
            bulk_screening_1, bulk_screening_3,
        ]
        bulk_screenings_ids = list(map(lambda bs: bs.id, bulk_screenings))

        env, resp = test_client.delete(self.uri, as_tuple=True)

        assert resp.status_code == 204
        assert not resp.data

        assert application.bulk_screenings_repository.find(
            id__in=bulk_screenings_ids) == []
        assert application.bulk_screenings_repository.find(
            id=bulk_screening_2.id) is not None


class TestScreeningBulkViewOptions:

    @pytest.fixture
    def bulk_screening(self, factory):
        account_id = 54321
        return factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.PENDING,
            result=None,
        )

    def get_uri(self, bulk_screening_id):
        return '/v1/screenings/_bulk/{0}'.format(bulk_screening_id)

    def test_allowed_methods(self, test_client, bulk_screening):
        env, resp = test_client.options(
            self.get_uri(bulk_screening.id), as_tuple=True)

        assert resp.status_code == 200
        assert set(resp.allow) == set(['OPTIONS', 'DELETE'])
        assert resp.headers['Access-Control-Allow-Origin'] == '*'


@pytest.mark.usefixtures('authenticated')
class TestScreeningBulkViewDelete:

    @pytest.fixture
    def bulk_screening(self, factory):
        account_id = 54321
        return factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.PENDING,
            result=None,
        )

    def get_uri(self, bulk_screening_id):
        return '/v1/screenings/_bulk/{0}'.format(bulk_screening_id)

    def test_unauthenticated(self, test_client, bulk_screening):
        test_client.environ_base['HTTP_AUTHORIZATION'] = ''

        env, resp = test_client.delete(
            self.get_uri(bulk_screening.id), as_tuple=True)

        assert resp.status_code == 401

    @freeze_time("2001-09-11 07:59:00")
    def test_valid(self, test_client, factory, application):
        account_id = 54321
        bulk_screening_1 = factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.PENDING,
            result=None,
        )
        bulk_screening_2 = factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.DONE,
            result=False,
        )
        bulk_screening_3 = factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.DONE,
            result=True,
        )
        bulk_screenings = [bulk_screening_1, bulk_screening_3]
        bulk_screenings_ids = list(map(lambda x: x.id, bulk_screenings))

        env, resp = test_client.delete(
            self.get_uri(bulk_screening_2.id), as_tuple=True)

        assert resp.status_code == 204
        assert not resp.data

        assert application.bulk_screenings_repository.find(
            id__in=bulk_screenings_ids) is not None
        assert application.bulk_screenings_repository.find(
            id=bulk_screening_2.id) == []
