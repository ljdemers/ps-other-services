# -*- coding: utf-8 -*-
class RemoteServiceError(Exception):
    """ Remote service returned a 500 error in a request. Remote service is
    broken or buggy. """
    pass


class ClientError(Exception):
    """ General Service client exception. Client's fault when dealing with an
    external/remote service. """
    pass


class NotFoundError(ClientError):
    """ Requested item not found when querying remote service. """
    pass


class UnexpectedStatusCode(Exception):
    pass


class MultipleObjectsReturnedError(Exception):
    pass
