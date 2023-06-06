class BaseGeoServerError(Exception):
    pass


class GeoServerResponseError(BaseGeoServerError):
    pass


class GeoServerResponseDecodeError(BaseGeoServerError):
    pass


class UnknownGeoServerError(BaseGeoServerError):
    pass
