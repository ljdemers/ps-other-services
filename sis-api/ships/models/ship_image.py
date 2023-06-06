import logging

from django.db import models

logger = logging.getLogger(__name__)


class ShipImage(models.Model):
    ship_data = models.ForeignKey(
        "ShipData", null=True, blank=True, on_delete=models.CASCADE
    )
    imo_id = models.CharField(max_length=32)
    source = models.CharField(max_length=255, null=True, blank=True)
    taken_date = models.DateTimeField(null=True, blank=True)
    url = models.URLField()
    filename = models.CharField(max_length=255)
    width = models.IntegerField()
    height = models.IntegerField()

    def __unicode__(self):
        return "%s" % self.url
