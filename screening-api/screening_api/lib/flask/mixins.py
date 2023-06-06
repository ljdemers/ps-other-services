from flask.globals import request


class HTTPMethodViewMixin(object):
    """Passes request object to dispached method."""

    def dispatch_request(self, *args, **kwargs):
        return super(HTTPMethodViewMixin, self).dispatch_request(
            request, *args, **kwargs)
