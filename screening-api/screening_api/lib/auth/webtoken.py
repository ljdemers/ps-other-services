import logging

import jwt

from screening_api.lib.auth.base import Authentication
from screening_api.lib.auth.exceptions import (
    NoAuthorizationHeader, InvalidAuthorizationHeader,
    InvalidAuthorizationSchema, ExpiredSignature,
    InvalidSignature, InvalidToken, InvalidPayload,
)
from screening_api.lib.auth.models import User

log = logging.getLogger(__name__)


class JWTAuthentication(Authentication):

    algorithms = ['HS256']
    authz_schema = 'Bearer'
    authz_header_name = 'Authorization'

    def __init__(self, secret_key):
        self.secret_key = secret_key

    def authenticate(self, request):
        token = self._get_token(request.headers)
        payload = self._get_payload(token)
        return self._get_user(payload)

    def _get_token(self, headers):
        log.debug("Getting token from headers")
        try:
            authz_value = headers[self.authz_header_name]
        except KeyError:
            raise NoAuthorizationHeader('No Authorization header.')

        try:
            schema, token = authz_value.split()
        except ValueError:
            raise InvalidAuthorizationHeader(
                'Invalid Authorization header. '
                'Credentials string should not contain spaces.'
            )

        if schema != self.authz_schema:
            raise InvalidAuthorizationSchema('Invalid Authorization schema.')

        return token

    def _get_payload(self, token):
        log.debug("Getting payload for token: {0}".format(token))
        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=self.algorithms,
            )
        except jwt.ExpiredSignature:
            raise ExpiredSignature('Signature has expired.')
        except jwt.DecodeError:
            raise InvalidSignature('Error decoding signature.')
        except jwt.InvalidTokenError:
            raise InvalidToken('Invalid token.')

    def _get_user(self, payload):
        log.debug("Getting user for payload: {0}".format(payload))
        try:
            return User(**payload)
        except TypeError:
            raise InvalidPayload('Invalid payload.')
