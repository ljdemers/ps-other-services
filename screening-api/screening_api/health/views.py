from screening_api import __name__, __version__
from screening_api.lib.flask.views import HTTPMethodView
from screening_api.lib.flask.responses import HTTPResponse, json
from screening_api.lib.health.indicators import Indicators


class LivenessView(HTTPMethodView):

    def get(self, request, *args, **kwargs):
        """
        A successful response means that service is up and running.
        """
        return HTTPResponse(status=204)


class ReadinessView(HTTPMethodView):

    def __init__(self, indicators: Indicators):
        self.indicators = indicators

    def get(self, request, *args, **kwargs):
        """
        A successful response means that other supporting services are running.
        """
        healths = self.indicators.get_healths()
        resp = {
            'name': __name__,
            'version': __version__,
            'services': healths.__json__(),
        }
        status = 200 if healths.is_healthy() else 503
        return json(resp, status=status)
