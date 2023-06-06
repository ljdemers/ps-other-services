import logging

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import fields

from ships.models.managers.ship_data import ShipDataManager

logger = logging.getLogger(__name__)


class ShipData(models.Model):
    class Meta:
        verbose_name = "ship"
        verbose_name_plural = "ships"

    objects = ShipDataManager()

    imo_id = fields.CharField(max_length=10, unique=True)
    mmsi = fields.CharField(
        max_length=10, null=True, blank=True, help_text="(9 digits)", db_index=True
    )
    ship_name = fields.CharField(max_length=255, null=True, blank=True, db_index=True)
    shiptype_level_5 = fields.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    call_sign = fields.CharField(max_length=255, null=True, blank=True, db_index=True)

    flag_name = fields.CharField(max_length=255, db_index=True, null=True, blank=True)
    flag = models.ForeignKey("Flag", null=True, blank=True, on_delete=models.CASCADE)

    port_of_registry = fields.CharField(
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
    )
    ship_status = fields.CharField(max_length=255, null=True, blank=True)

    gross_tonnage = fields.FloatField(null=True, blank=True, db_index=True)
    length_overall_loa = fields.FloatField(null=True, blank=True, db_index=True)
    year_of_build = fields.IntegerField(null=True, blank=True, db_index=True)

    registered_owner = fields.CharField(
        max_length=255, db_index=True, null=True, blank=True
    )
    operator = fields.CharField(max_length=255, db_index=True, null=True, blank=True)
    ship_manager = fields.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    technical_manager = fields.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    group_beneficial_owner = fields.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )

    data = JSONField()  # Things not covered by an attribute
    updated = fields.DateTimeField(auto_now=True)
    # Field requested by p1c3u, to keep copy of data before manual changes
    original_data = JSONField(null=True, blank=True, default=dict)

    def to_dict(self):
        data = self.data
        data["flag"] = None
        if self.flag:
            data["flag"] = self.flag.to_dict()
        return data

    def __str__(self):
        return "{} {}".format(self.imo_id, self.ship_name)
