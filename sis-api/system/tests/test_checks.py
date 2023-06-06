from datetime import datetime, timedelta

from django.test import TestCase
from unittest.mock import patch
from freezegun import freeze_time

from ships.models import LoadStatus, LoadHistory
from system import tasks
from system.checks import CeleryBeatCheck, FailedLoadHistoryCheck


class FailedLoadsCheckTest(TestCase):

    def tearDown(self):
        LoadStatus.objects.all().delete()
        LoadHistory.objects.all().delete()

    def test_run_no_loads(self):
        actual = FailedLoadHistoryCheck().value
        self.assertEqual('ERROR', actual)

    def test_run_load_failed(self):
        LoadHistory.objects.create(status=LoadStatus.FAILED)
        actual = FailedLoadHistoryCheck().value
        self.assertEqual('WARNING', actual)

    def test_run_load_failed_and_succeeded(self):
        LoadHistory.objects.create(status=LoadStatus.FAILED)
        actual = FailedLoadHistoryCheck().value
        self.assertEqual('WARNING', actual)

        ls = LoadHistory.objects.create(status=LoadStatus.SUCCEEDED)
        actual = FailedLoadHistoryCheck().value
        self.assertEqual('OK', actual)

    def test_run_old_load(self):
        load_datetime = datetime.now() - timedelta(days=5)
        LoadHistory.objects.create(status=LoadStatus.SUCCEEDED,
                                   started_date=load_datetime)
        actual = FailedLoadHistoryCheck().value
        self.assertEqual('WARNING', actual)

    def test_run_ok(self):
        LoadHistory.objects.create(status=LoadStatus.SUCCEEDED)
        actual = FailedLoadHistoryCheck().value
        self.assertEqual('OK', actual)


class HeartbeatTest(TestCase):

    @patch('system.tasks.cache.get', return_value=None)
    @freeze_time('2001-09-11 9:15:00')
    def test_no_beat(self, m_cache):
        check = CeleryBeatCheck()
        tasks.heartbeat()

        result = check.run()

        assert result == 'ERROR'

    @patch(
        'system.tasks.cache.get',
        return_value=datetime(2001, 9, 11, 8, 0, 0),
    )
    @freeze_time('2001-09-11 9:15:00')
    def test_timed_out(self, m_cache):
        check = CeleryBeatCheck()
        tasks.heartbeat()

        result = check.run()

        assert result == 'ERROR'

    @patch(
        'system.tasks.cache.get',
        return_value=datetime(2001, 9, 11, 9, 16, 0),
    )
    @freeze_time('2001-09-11 9:15:00')
    def test_beat(self, m_cache):
        check = CeleryBeatCheck()
        tasks.heartbeat()

        result = check.run()

        assert result == 'OK'
