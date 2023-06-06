class BaseAuthenticationError(Exception):
    pass


class AuthenticationHeaderError(BaseAuthenticationError):
    pass


class AuthenticationTokenError(BaseAuthenticationError):
    pass


class NoAuthorizationHeader(AuthenticationHeaderError):
    pass


class InvalidAuthorizationHeader(AuthenticationHeaderError):
    pass


class InvalidAuthorizationSchema(AuthenticationHeaderError):
    pass


class ExpiredSignature(AuthenticationTokenError):
    pass


class InvalidSignature(AuthenticationTokenError):
    pass


class InvalidToken(AuthenticationTokenError):
    pass


class InvalidPayload(AuthenticationTokenError):
    pass
