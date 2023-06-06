from requests.exceptions import HTTPError

from screening_workers.lib.messaging.tasks import CountdownRetryTask
from screening_workers.lib.screening.checks import CheckInterface


class CheckTask(CountdownRetryTask):
    """
    Celery task that performs a provided check.
    """
    task_serializer = 'extended-json'
    retry_errors = (HTTPError, )

    def __init__(self, check: CheckInterface, soft_time_limit: int =None):
        self.check = check
        self.soft_time_limit = soft_time_limit

    def get_countdown(self):
        return 2 ** self.request.retries

    def retry_run(self, screening_id: int):
        return self.check.do_check(screening_id)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.check.on_failure(*args, **kwargs)
