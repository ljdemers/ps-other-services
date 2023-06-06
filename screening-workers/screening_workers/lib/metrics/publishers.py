import statsd


class MetricsPublisher(object):

    def increase(self, name: str, count: int = 1, rate: int = 1):
        raise NotImplementedError

    def time(self, stat: str, delta: int, rate: int = 1):
        raise NotImplementedError


class StatsDMetricsPublisher(MetricsPublisher):

    def __init__(self, address='127.0.0.1', port=8125, prefix=None):
        self.client = statsd.StatsClient(
            host=address, port=port, prefix=prefix)

    def increase(
        self, stat: str,
        count: int = 1, rate: int = 1, dimensions: dict = None,
    ):
        self.client.incr(stat, count=count, rate=rate, tags=dimensions)

    def time(
        self, stat: str, delta: int,
        rate: int = 1, dimensions: dict = None,
    ):
        self.client.timing(stat, delta=delta, rate=rate, tags=dimensions)
