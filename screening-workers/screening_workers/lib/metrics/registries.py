from celery.five import monotonic


class TimersRegistry(dict):

    def start(self, timer_id):
        self[timer_id] = monotonic()

    def end(self, timer_id):
        time_start = self.get(timer_id)
        if time_start is None:
            return

        delta_secs = monotonic() - time_start
        return delta_secs * 1000
