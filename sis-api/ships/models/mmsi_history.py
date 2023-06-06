import logging

from django.db import models
from django.utils import timezone

from ships.models.ship_data import ShipData

logger = logging.getLogger(__name__)


class MMSIHistory(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    imo_number = models.CharField(max_length=7, blank=False, null=False)
    mmsi = models.CharField(max_length=15, blank=False, null=False)
    effective_from = models.DateTimeField(
        blank=False,
        null=False,
        default=timezone.now,
    )
    effective_to = models.DateTimeField(blank=True, null=True, default=None)

    objects = models.Manager()

    class Meta:
        verbose_name = "mmsi_history"
        verbose_name_plural = "MMSI Histories"
        unique_together = ("imo_number", "mmsi")

    def __str__(self):
        return "IMO Number: {0} MMSI Number: {1} ({2} - {3})".format(
            self.imo_number,
            self.mmsi,
            self.effective_from,
            self.effective_to,
        )

    def save(self, *args, **kwargs):
        # save the new mmsi in ship data
        try:
            ship_data = ShipData.objects.filter(imo_id=self.imo_number)[0]
            ship_data.mmsi = self.mmsi
            ship_data.save()
        except IndexError as e:
            msg = "{} for imo {}".format(str(e), self.imo_number)
            logger.exception(msg)
            pass

        # store MMSIHistory
        super().save(*args, **kwargs)
