from functools import partialmethod
import logging

from celery import Task

from screening_workers.lib.metrics.enums import MetricsEvent
from screening_workers.lib.metrics.publishers import MetricsPublisher
from screening_workers.lib.metrics.registries import TimersRegistry

log = logging.getLogger(__name__)


class CeleryMetricsConnector(object):

    def __init__(self, publisher: MetricsPublisher, namespace: str = ''):
        self.publisher = publisher
        self.namespace = namespace

        self._timers = TimersRegistry()

    def connect(self, signals):
        log.debug("Celery Metrics connecting")
        signals.task_retry.connect(weak=False)(self.on_retry)
        signals.task_success.connect(weak=False)(self.on_success)
        signals.task_failure.connect(weak=False)(self.on_failure)
        signals.task_revoked.connect(weak=False)(self.on_revoked)
        signals.task_prerun.connect(weak=False)(self.on_prerun)
        signals.task_postrun.connect(weak=False)(self.on_postrun)

    # timers

    def on_prerun(self, sender: Task, **kwargs):
        log.debug("Recording prerun time on %s celery task", sender)
        self._timers.start(sender.request.id)

    def on_postrun(self, sender: Task, **kwargs):
        log.debug("Recording postrun time on %s celery task", sender)
        delta_milis = self._timers.end(sender.request.id)
        if delta_milis is None:
            log.debug(
                "Prerun time on %s celery task wasn't recorded",
                sender,
            )
            return

        event = MetricsEvent.TASK_TIME
        name = self._get_task_metric_name(sender, event)
        dimensions = self._get_task_metric_dimensions(sender, event)
        self._publish_time(name, delta_milis, dimensions)

    # counters

    def on_event_count(self, event: MetricsEvent, sender: Task, **kwargs):
        name = self._get_task_metric_name(sender, event)
        dimensions = self._get_task_metric_dimensions(sender, event)
        self._publish_increase(name, dimensions)

    on_retry = partialmethod(on_event_count, event=MetricsEvent.TASK_RETRY)
    on_success = partialmethod(on_event_count, event=MetricsEvent.TASK_SUCCESS)
    on_failure = partialmethod(on_event_count, event=MetricsEvent.TASK_FAILURE)
    on_revoked = partialmethod(on_event_count, event=MetricsEvent.TASK_REVOKED)

    def _publish_time(self, name, delta_milis, dimensions=None):
        log.debug("Publishing metric %s time on %s", delta_milis, name)
        self.publisher.time(name, delta_milis, dimensions=dimensions)

    def _publish_increase(self, name, dimensions=None):
        log.debug("Publishing metric count on %s", name)
        self.publisher.increase(name, dimensions=dimensions)

    def _get_task_name(self, task):
        if not isinstance(task, str):
            return task.name

        return task

    def _get_task_metric_name(self, task, event):
        if not self.namespace:
            return event.value

        return f'{self.namespace}.{event.value}'

    def _get_task_metric_dimensions(self, task, event):
        task_name = self._get_task_name(task)
        return {
            'Application': 'screening',
            'Component': 'workers',
            'TaskName': task_name,
            'Hostname': task.request.hostname,
        }
