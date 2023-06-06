import logging

from django.db import models

logger = logging.getLogger(__name__)


class ShipInspectionManager(models.Manager):
    def import_data(self, attrs=None, data=None):
        """
        Import a single ship inspection
        """
        pkname = "inspection_id"
        pk = attrs[pkname]
        if attrs.get("inspection_date"):
            attrs["inspection_date"] = attrs["inspection_date"].split(" ")[0]
        if not self.filter(**{pkname: pk}).update(**attrs):
            self.create(**attrs)
