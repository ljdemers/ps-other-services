from datetime import datetime, timezone

from celery.schedules import crontab
import pytest
from freezegun import freeze_time
from redbeat.schedulers import redis, RedBeatSchedulerEntry

from screening_api.lib.health.enums import HealthStatus

from screening_workers import __version__
from screening_workers.lib.health.tasks import HeartbeatTask


class TestHeartbeatTask:

    @pytest.fixture
    def task(self, application):
        return application.tasks[HeartbeatTask.name]

    @pytest.fixture
    def redis(self, application):
        return redis(app=application)

    @pytest.yield_fixture
    def redbeat(self, application, redis):
        def clear_redbeat(client, key_prefix):
            key_regex = "{0}*".format(key_prefix)
            for key in client.scan_iter(key_regex):
                client.delete(key)
        clear_redbeat(redis, application.redbeat_conf.key_prefix)
        yield redis
        clear_redbeat(redis, application.redbeat_conf.key_prefix)

    @freeze_time("2001-09-11 07:59:00")
    @pytest.yield_fixture
    def entry(self, application):
        def nowfun():
            return datetime(2001, 9, 11, 7, 58, 0, tzinfo=timezone.utc)
        entry = RedBeatSchedulerEntry(
            name='test_task()', task='test_task', app=application,
            schedule=crontab(nowfun=nowfun),
        )
        entry.save()
        yield entry
        entry.delete()

    def test_registered(self, application):
        assert HeartbeatTask.name in application.tasks

    @pytest.mark.skip(reason="Since ports is now internal service. "
                             "This will fail, so skip for now")
    @freeze_time("2001-09-11 07:59:00")
    def test_updated_no_schedules(
            self, task, heartbeat_cache, redbeat, portservice_client):
        result = task.apply()

        result_value = result.get()

        assert result_value is None

        cache_value = heartbeat_cache.get('heartbeat')
        assert cache_value == {
            'timestamp': datetime(2001, 9, 11, 7, 59, 0),
            'version': __version__,
            'hostname': None,
            'tasks': [
                'celery.accumulate',
                'celery.backend_cleanup',
                'celery.chain',
                'celery.chord',
                'celery.chord_unlock',
                'celery.chunks',
                'celery.group',
                'celery.map',
                'celery.ping',
                'celery.starmap',
                'heartbeat',
                'screening.bulk_screenings.validation',
                'screening.company_sanctions.ship_beneficial_owner_check',
                'screening.company_sanctions.ship_company_associates_check',
                'screening.company_sanctions.ship_manager_check',
                'screening.company_sanctions.ship_operator_check',
                'screening.company_sanctions.ship_registered_owner_check',
                'screening.company_sanctions.ship_technical_manager_check',
                'screening.country_sanctions.doc_company_check',
                'screening.country_sanctions.ship_beneficial_owner_check',
                'screening.country_sanctions.ship_flag_check',
                'screening.country_sanctions.ship_manager_check',
                'screening.country_sanctions.ship_operator_check',
                'screening.country_sanctions.ship_registered_owner_check',
                'screening.country_sanctions.ship_technical_manager_check',
                'screening.screenings.bulk_screen',
                'screening.screenings.bulk_screen_killer',
                'screening.screenings.screen',
                'screening.screenings.screen_killer',
                'screening.ship_inspections.ship_inspections_check',
                'screening.ship_movements.port_visits_check',
                'screening.ship_movements.zone_visits_check',
                'screening.ship_sanctions.ship_association_check',
                'screening.ship_sanctions.ship_sanction_check',
                'screening.ships.ship_cache_update',
                'screening.ships.ships_cache_update',
            ],
            'schedules': [],
            'services': [
                {
                    'errors': [],
                    'notes': {'drivername': 'postgresql+psycopg2'},
                    'service_type': 'database',
                    'status': HealthStatus.PASSING,
                },
                {
                    'errors': [],
                    'notes': {
                        'server_url': portservice_client.server_url,
                    },
                    'service_type': 'ports',
                    'status': HealthStatus.PASSING,
                },
            ],
        }

    @pytest.mark.skip(reason="Since ports is now internal service. "
                             "This will fail, so skip for now")
    @freeze_time("2001-09-11 07:59:00")
    def test_updated_schedules(
            self, application, task, heartbeat_cache, redbeat, entry,
            portservice_client):
        redbeat.zadd(
            application.redbeat_conf.schedule_key, entry.score, entry.key)
        result = task.apply()

        result_value = result.get()

        assert result_value is None

        cache_value = heartbeat_cache.get('heartbeat')
        assert cache_value == {
            'timestamp': datetime(2001, 9, 11, 7, 59, 0),
            'version': __version__,
            'hostname': None,
            'tasks': [
                'celery.accumulate',
                'celery.backend_cleanup',
                'celery.chain',
                'celery.chord',
                'celery.chord_unlock',
                'celery.chunks',
                'celery.group',
                'celery.map',
                'celery.ping',
                'celery.starmap',
                'heartbeat',
                'screening.bulk_screenings.validation',
                'screening.company_sanctions.ship_beneficial_owner_check',
                'screening.company_sanctions.ship_company_associates_check',
                'screening.company_sanctions.ship_manager_check',
                'screening.company_sanctions.ship_operator_check',
                'screening.company_sanctions.ship_registered_owner_check',
                'screening.company_sanctions.ship_technical_manager_check',
                'screening.country_sanctions.doc_company_check',
                'screening.country_sanctions.ship_beneficial_owner_check',
                'screening.country_sanctions.ship_flag_check',
                'screening.country_sanctions.ship_manager_check',
                'screening.country_sanctions.ship_operator_check',
                'screening.country_sanctions.ship_registered_owner_check',
                'screening.country_sanctions.ship_technical_manager_check',
                'screening.screenings.bulk_screen',
                'screening.screenings.bulk_screen_killer',
                'screening.screenings.screen',
                'screening.screenings.screen_killer',
                'screening.ship_inspections.ship_inspections_check',
                'screening.ship_movements.port_visits_check',
                'screening.ship_movements.zone_visits_check',
                'screening.ship_sanctions.ship_association_check',
                'screening.ship_sanctions.ship_sanction_check',
                'screening.ships.ship_cache_update',
                'screening.ships.ships_cache_update',
            ],
            'schedules': [
                {
                    'task': entry.task,
                    'total_run_count': entry.total_run_count,
                    'last_run_at': None,
                    'due_at': entry.due_at,
                },
            ],
            'services': [
                {
                    'errors': [],
                    'notes': {'drivername': 'postgresql+psycopg2'},
                    'service_type': 'database',
                    'status': HealthStatus.PASSING,
                },
                {
                    'errors': [],
                    'notes': {
                        'server_url': portservice_client.server_url,
                    },
                    'service_type': 'ports',
                    'status': HealthStatus.PASSING,
                },
            ],
        }
