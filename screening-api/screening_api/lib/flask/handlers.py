import sys

from flask._compat import reraise
from werkzeug.exceptions import HTTPException


class LogExceptionsHandler:

    def __init__(self, app, logger):
        self.app = app
        self.logger = logger

    def __call__(self, exc):
        if isinstance(exc, HTTPException):
            return exc

        self.logger.critical("Unhandled exception: {0}".format(exc))
        exc_type, exc_value, tb = sys.exc_info()
        reraise(exc_type, exc_value, tb)
