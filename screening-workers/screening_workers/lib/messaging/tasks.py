from celery import Task


class CountdownRetryTask(Task):

    retry_errors = NotImplemented

    def get_countdown(self):
        raise NotImplementedError

    def run(self, *args, **kwargs):
        try:
            return self.retry_run(*args, **kwargs)
        except self.retry_errors as exc:
            countdown = self.get_countdown()
            raise self.retry(
                args=args, kwargs=kwargs, countdown=countdown, exc=exc)

    def retry_run(self, *args, **kwargs):
        raise NotImplementedError


class CacheUpdateTask(Task):

    def __init__(self, cache):
        self.cache = cache

    def run(self, *args, **kwargs):
        self.cache.update(self.request.origin)
