"""
Django-based backend which looks up ships using the database
"""
import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from ships import models

log = logging.getLogger(__name__)

list_attrs = ['imo_id', 'mmsi', 'ship_name', 'call_sign', 'date_of_build',
              'deadweight', 'flag_name', 'gross_tonnage', 'port_of_registry',
              'shiptype_level_5']


class CacheBackend(object):
    @staticmethod
    def get_ship_by_mmsi(mmsi):
        if not isinstance(mmsi, (list, tuple)):
            mmsi = [mmsi]
        try:
            ship = models.ShipData.objects.get(mmsi__in=mmsi)
            return ship.to_dict()
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def get_ship_by_imo(imo_id):
        if not isinstance(imo_id, (list, tuple)):
            imo_id = [imo_id]
        try:
            ship = models.ShipData.objects.get(imo_id__in=imo_id)
            return ship.to_dict()
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def list_updated_ships(updated_since, imo_ids):
        ships = models.ShipData.objects.filter(imo_id__in=imo_ids,
                                               updated__gt=updated_since)
        result = []
        for ship in ships:
            data = ship.to_dict()
            result.append(data)
        return result

    @staticmethod
    def list_ships_by_name(names):
        if not isinstance(names, (list, tuple)):
            names = [names]
        expr = Q()
        for name in names:
            expr.add(("ship_name__icontains", name), Q.OR)
        data = models.ShipData.objects.filter(expr)
        result = []
        for ship in data:
            result.append(ship.to_dict())
        return result
