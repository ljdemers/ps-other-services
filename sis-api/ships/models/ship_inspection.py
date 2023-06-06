import logging

from django.db import models
from django.db.models import fields

from ships.models.managers.ship_inspection import ShipInspectionManager

logger = logging.getLogger(__name__)


class ShipInspection(models.Model):

    objects = ShipInspectionManager()

    inspection_id = fields.CharField(max_length=50, primary_key=True)
    imo_id = fields.CharField(max_length=10, db_index=True, null=True, blank=True)
    authorisation = fields.CharField(max_length=255, null=True, blank=True)
    ship_name = fields.CharField(max_length=255, null=True, blank=True)
    call_sign = fields.CharField(max_length=255, null=True, blank=True)
    flag_name = fields.CharField(max_length=255, null=True, blank=True)
    shipclass = fields.CharField(max_length=255, null=True, blank=True)
    shiptype = fields.CharField(max_length=255, null=True, blank=True)
    expanded_inspection = fields.BooleanField()
    inspection_date = fields.CharField(
        max_length=50, null=True, blank=True
    )  # FIXME: This can use a `DateField`. The import logic must be fixed too.
    date_release = fields.CharField(
        max_length=50, null=True, blank=True
    )  # FIXME: This can use a `DateField`. The import logic must be fixed too.
    no_days_detained = fields.IntegerField(null=True, blank=True)
    port_name = fields.CharField(max_length=255, null=True, blank=True)
    country_name = fields.CharField(max_length=255, null=True, blank=True)
    owner = fields.CharField(max_length=255, null=True, blank=True)
    manager = fields.TextField(blank=True, null=True)
    charterer = fields.CharField(max_length=255, null=True, blank=True)
    cargo = fields.CharField(max_length=30, null=True, blank=True)
    detained = fields.BooleanField()
    no_defects = fields.IntegerField(null=True, blank=True)
    source = fields.CharField(max_length=255, null=True, blank=True)
    gt = fields.IntegerField(null=True, blank=True, help_text="Gross tonnage")
    dwt = fields.IntegerField(null=True, blank=True, help_text="Deadweight tonnage")
    yob = fields.SmallIntegerField(null=True, blank=True, help_text="Year of build")
    other_inspection_type = fields.CharField(max_length=255, null=True, blank=True)
    number_part_days_detained = fields.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
