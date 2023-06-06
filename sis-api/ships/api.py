# -*- coding: utf8 -*-
import datetime
import logging

from dateutil.relativedelta import relativedelta
from django.db.models import Q
from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource

from ships import models
from ships.backend import Broker
from sis_api.utils import DictObject, TopResource

log = logging.getLogger(__name__)


class RestrictedAuthentication(ApiKeyAuthentication):
    """
    Allows unauthenticated GET access, but denies modification unless
    credentials are provided
    """

    def is_authenticated(self, request, **kwargs):
        # Use django session auth when possible. Makes it simpler to debug.
        if request.method in ('GET', 'HEAD', 'OPTIONS'
                              ) and request.user.is_authenticated:
            return True

        return super(RestrictedAuthentication, self).is_authenticated(
            request, **kwargs
        )


class DefectsResource(ModelResource):
    inspection = fields.ForeignKey(
        'ships.api.InspectionsResource', 'inspection'
    )

    class Meta:
        object_class = models.ShipDefect
        queryset = models.ShipDefect.objects.all()
        allowed_methods = ['get']
        authorization = ReadOnlyAuthorization()
        authentication = RestrictedAuthentication()
        exclude = ['defects']


class InspectionsResource(ModelResource):
    defects = fields.ToManyField(DefectsResource, 'defects', full=True)

    class Meta:
        object_class = models.ShipInspection
        queryset = models.ShipInspection.objects.all().order_by(
            "-inspection_date")
        allowed_methods = ['get']
        authorization = ReadOnlyAuthorization()
        authentication = RestrictedAuthentication()
        filtering = {'imo_id': ALL}


class ShipInspectionsResource(ModelResource):
    """ Provides an alias to searching for inspections by ``imo_id``. """
    class Meta:
        object_class = models.ShipInspection
        allowed_methods = ['get']
        detail_uri_name = 'inspection_id'
        resource_name = 'inspections'

    def get_list(self, request, **kwargs):
        return InspectionsResource().get_list(request, **kwargs)

    def get_detail(self, request, **kwargs):
        """
        Retrieve a single resource as a value dict, wrapping it as an object.
        """
        return InspectionsResource().get_detail(request, **kwargs)


class FlagResource(ModelResource):

    class Meta:
        queryset = models.Flag.objects.all()
        resource_name = 'flag'
        allowed_methods = ['get']
        authentication = RestrictedAuthentication()
        authorization = ReadOnlyAuthorization()
        filtering = {
            'code': ALL,
            'name': ALL,
            'alt_name': ALL,
            'world_region': ALL,
            'world_continent': ALL,
            'iso_3166_1_alpha_2': ALL
        }


class ShipResource(ModelResource):
    """
    Ships resource. Data come from ``ShipData`` model. See also ShipsResource.
    """
    image = fields.CharField(
        attribute='image', null=True, blank=True, help_text='Ship Image'
    )
    thumbnail = fields.CharField(
        attribute='thumbnail', null=True, blank=True,
        help_text='Ship thumbnail Image'
    )
    flag = fields.ForeignKey(FlagResource, 'flag', null=True, full=True)
    data = fields.DictField(attribute='data')

    class Meta:
        queryset = models.ShipData.objects.all().distinct('id').select_related(
            'flag').prefetch_related('shipimage_set')
        resource_name = 'ship'
        allowed_methods = ['get']
        authentication = RestrictedAuthentication()
        authorization = ReadOnlyAuthorization()
        filtering = {
            "imo_id": ALL,
            "ship_name": ALL,
            "shiptype_level_5": ALL,
            "mmsi": ALL,
            "call_sign": ALL,
            "flag": ALL_WITH_RELATIONS,
            "registered_owner": ALL,
            "operator": ALL,
            "gross_tonnage": ALL,
            "length_overall_loa": ALL,
            "year_of_build": ALL,
            "technical_manager": ALL,
            "group_beneficial_owner": ALL,
            "ship_manager": ALL
        }

    def dehydrate(self, bundle):
        images = list(bundle.obj.shipimage_set.all())
        images.sort(key=lambda x: (x.width, x.height), reverse=True)
        if images:
            bundle.data['image'] = images[0].url
            bundle.data['thumbnail'] = images[-1].url
        return bundle

    def apply_filters(self, request, applicable_filters):
        queryset = self.get_object_list(request).filter(**applicable_filters)

        complex_query = request.GET.get('q')
        if complex_query is not None:
            queryset = queryset.filter(
                Q(
                    ship_name__istartswith=complex_query
                ) | Q(
                    imo_id__istartswith=complex_query
                )
            )

        return queryset


class ShipsResource(TopResource):
    """
    Ships resource. Data come from ``data`` field in ``ShipData`` model.
    """
    imo_id = fields.CharField(attribute='imo_id', help_text='IMO number')
    mmsi = fields.CharField(
        attribute='mmsi', null=True, blank=True,
        help_text='MMSI identifier (9 digits)'
    )
    ship_name = fields.CharField(
        attribute='ship_name', null=True, blank=True, help_text='Ship name'
    )
    image = fields.CharField(
        attribute='image', null=True, blank=True, help_text='Ship Image'
    )
    thumbnail = fields.CharField(
        attribute='thumbnail', null=True, blank=True,
        help_text='Ship thumbnail Image'
    )

    nested_resources = {'inspections': ShipInspectionsResource()}
    broker = Broker()
    DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

    class Meta:
        object_class = DictObject
        authorization = ReadOnlyAuthorization()
        authentication = RestrictedAuthentication()
        allowed_methods = ['get']
        detail_uri_name = 'imo_id'
        filtering = {
            "imo_id": ['exact', 'in'],
        }

    def get_object_list(self, bundle, **kwargs):
        filters = {}
        if hasattr(bundle.request, 'GET'):
            for name in bundle.request.GET:
                value = [v for v in bundle.request.GET.getlist(name) if v]
                if value:
                    filters[name] = value
        filters.update(kwargs)
        if 'updated' in filters:
            try:
                updated = datetime.datetime.strptime(filters['updated'][0],
                                                     self.DATE_FORMAT)
            except ValueError:
                updated = filters['updated'][0]  # pass to postgres
            result = self.broker.list_updated_ships(
                updated, filters.get('imo_id', []))
            return result
        if 'imo_id' in filters:
            result = []
            for key in filters['imo_id']:
                data = self.broker.get_ship_by_imo(key)
                if data:
                    result.append(data)
            return result
        if 'imo_id__in' in filters:
            result = []
            for key in filters['imo_id__in'][0].split(','):
                data = self.broker.get_ship_by_imo(key)
                if data:
                    result.append(data)
            return result
        if 'mmsi' in filters:
            result = []
            for key in filters['mmsi']:
                data = self.broker.get_ship_by_mmsi(key)
                if data:
                    result.append(data)
            return result
        if 'ship_name' in filters:
            return self.broker.list_ships_by_name(filters['ship_name'])
        return []

    # FIXME: The imo_id is either string or dict...
    def get_object(self, imo_id):
        if isinstance(imo_id, dict):
            if 'imo_id' in imo_id:
                return imo_id
            else:
                return None  # Only return ships that have IMO ID defined

        return self.broker.get_ship_by_imo(imo_id)

    def dehydrate(self, bundle):
        for attr, value in bundle.obj.to_dict().items():
            if attr not in bundle.data:
                bundle.data[attr] = value

        images = list(models.ShipImage.objects.filter(
            ship_data__imo_id=bundle.data["imo_id"]).order_by("-width",
                                                              "-height"))
        if images:
            bundle.data["image"] = images[0].url
            bundle.data["thumbnail"] = images[-1].url

        return bundle


class ShipImageResource(ModelResource):

    class Meta:
        queryset = models.ShipImage.objects.all().order_by("-width", "-height")
        allowed_methods = ['get']
        authorization = ReadOnlyAuthorization()
        authentication = RestrictedAuthentication()
        filtering = {'imo_id': ALL}


class ShipTypeResource(ModelResource):

    class Meta:
        resource_name = 'shiptype'
        fields = ['shiptype_level_5']
        queryset = models.ShipData.objects\
            .filter(shiptype_level_5__isnull=False)\
            .distinct('shiptype_level_5')\
            .order_by('shiptype_level_5')
        allowed_methods = ['get']
        authorization = ReadOnlyAuthorization()
        authentication = RestrictedAuthentication()
        filtering = {'shiptype_level_5': ALL}

    def dehydrate(self, bundle):
        del bundle.data['resource_uri']
        return bundle


class ShipMovementResource(ModelResource):

    class Meta:
        resource_name = 'ship_movement'
        queryset = models.ShipMovement.objects.all().order_by('timestamp')
        allowed_methods = ['get']
        authorization = ReadOnlyAuthorization()
        authentication = RestrictedAuthentication()
        filtering = {
            'imo_id': ['exact', 'in'],
            'timestamp': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'port_name': ALL_WITH_RELATIONS,
            'country_name': ALL_WITH_RELATIONS,
            'hours_in_port': ALL_WITH_RELATIONS,
            'sail_date_full': ALL_WITH_RELATIONS,
        }
        ordering = ['id', 'timestamp', 'sail_date_full']


class MMSIHistoryResource(ModelResource):

    class Meta:
        queryset = models.MMSIHistory.objects.all()
        resource_name = 'mmsi_history'
        allowed_methods = ['get']
        authorization = ReadOnlyAuthorization()
        authentication = RestrictedAuthentication()
        filtering = {
            'created': ALL,
            'modified': ALL,
            'imo_number': ALL,
            'mmsi': ALL,
            'effective_from': ALL,
            'effective_to': ALL,
        }
        ordering = ['effective_from', 'effective_to']

    def build_filters(self, filters=None, ignore_bad_filters=False):
        qs_filters = super(MMSIHistoryResource, self).build_filters(
            filters=filters, ignore_bad_filters=ignore_bad_filters)

        # custom effective delta filter
        if filters and 'effective_delta' in filters:
            value = filters['effective_delta']
            # year delta support
            if value == 'year':
                value = relativedelta(years=1)
                qs_filters['effective_delta'] = value

        return qs_filters

    def apply_filters(self, request, applicable_filters):
        effective_delta = applicable_filters.pop(
            'effective_delta', None)

        qs = super(MMSIHistoryResource, self).apply_filters(
            request, applicable_filters)

        if effective_delta is not None:
            today = datetime.date.today()
            effective_date = today - effective_delta
            effective_delta_filter = (
                Q(
                    effective_to__isnull=False,
                    effective_to__gte=effective_date,
                ) |
                Q(
                    effective_to__isnull=True,
                )
            )
            qs = qs.filter(effective_delta_filter)

        return qs


class IMOResource(ModelResource):

    class Meta:
        queryset = models.ShipData.objects.all().order_by('imo_id')
        resource_name = 'imos'
        allowed_methods = ['get']
        fields = ['imo_id']
        include_resource_uri = False
        authorization = ReadOnlyAuthorization()
        authentication = RestrictedAuthentication()
        limit = 10000
        max_limit = 10000


class FlagHistoryResource(ModelResource):

    flag = fields.ForeignKey(FlagResource, 'flag', null=True, full=True)

    class Meta:
        queryset = models.FlagHistory.objects.all().select_related('flag')
        resource_name = 'flag_history'
        allowed_methods = ['get']
        fields = ['timestamp', 'imo_id', 'flag', 'flag_name', 'flag_effective_date', 'ignore']
        authentication = RestrictedAuthentication()
        authorization = ReadOnlyAuthorization()
        filtering = {
            'imo_id': ['exact', 'in'],
            'ignore': ['exact']
        }
        ordering = ['timestamp', 'flag_effective_date']


class CompanyHistoryResource(ModelResource):

    class Meta:
        queryset = models.CompanyHistory.objects.all()
        resource_name = 'company_history'
        allowed_methods = ['get']
        excludes = ['id', 'manual_edit', 'ship_history']
        authentication = RestrictedAuthentication()
        authorization = ReadOnlyAuthorization()
        filtering = {
            'imo_id': ['exact', 'in'],
            'ignore': ['exact'],
        }
        ordering = ['effective_date']
