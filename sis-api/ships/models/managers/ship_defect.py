import logging

from django.db import models

from ships.models.ship_inspection import ShipInspection

logger = logging.getLogger(__name__)


class ShipDefectManager(models.Manager):
    def import_data(self, attrs=None, data=None):
        """
        Import a single ship defect
        """
        pkname = "defect_id"
        pk = attrs[pkname]
        attrs["inspection"] = ShipInspection.objects.get(pk=data["inspection_id"])
        if not self.filter(**{pkname: pk}).update(**attrs):
            self.create(**attrs)
