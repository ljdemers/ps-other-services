from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from tastypie.api import Api

from sis_api.utils import SystemResource
from ships.api import (ShipsResource, ShipResource, InspectionsResource,
                       DefectsResource, ShipImageResource,
                       ShipTypeResource, IMOResource, ShipMovementResource,
                       MMSIHistoryResource, FlagHistoryResource, CompanyHistoryResource)
from ports.api import PortsResource, CountriesResource

admin.autodiscover()


api = Api(api_name='v1')
api.register(ShipResource())
api.register(ShipsResource())
api.register(InspectionsResource())
api.register(DefectsResource())
api.register(PortsResource())
api.register(CountriesResource())
api.register(ShipImageResource())
api.register(SystemResource())
api.register(ShipTypeResource())
api.register(ShipMovementResource())
api.register(IMOResource())
api.register(MMSIHistoryResource())
api.register(FlagHistoryResource())
api.register(CompanyHistoryResource())


urlpatterns = [
    url(r'^api/', include(api.urls)),
    url(r'^admin/', admin.site.urls),
]

if getattr(settings, "DEBUG", False):
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
