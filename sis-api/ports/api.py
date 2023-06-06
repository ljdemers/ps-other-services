from tastypie import resources
from ports.models import Port, Country


class CountriesResource(resources.ModelResource):

    class Meta:
        object_class = Country
        query_set = Country.objects.all()


class PortsResource(resources.ModelResource):

    class Meta:
        object_class = Port
        query_set = Port.objects.all()
