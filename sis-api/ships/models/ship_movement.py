import logging

from django.db import models
from django.db.models import fields

from ships.models.managers.ship_movement import ShipMovementManager

logger = logging.getLogger(__name__)


class ShipMovement(models.Model):

    imo_id = fields.CharField(max_length=10, db_index=True, null=True, blank=True)
    arrival_date = models.DateField(max_length=127, blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True, db_index=True)
    ihs_id = fields.CharField(max_length=127, db_index=True, null=True, blank=True)
    country_name = fields.CharField(max_length=127, null=True, blank=True)
    ihs_creation_date = models.DateTimeField(blank=True, null=True)
    destination_port = fields.CharField(max_length=127, null=True, blank=True)
    estimated_time_of_arrival = models.DateTimeField(blank=True, null=True)
    hours_in_port = models.IntegerField(blank=True, null=True)

    last_port_of_call_arrival_date = models.DateTimeField(blank=True, null=True)

    last_port_of_call_code = fields.CharField(max_length=127, null=True, blank=True)
    last_port_of_call_country = fields.CharField(max_length=127, null=True, blank=True)
    last_port_of_call_country_code = fields.CharField(
        max_length=127, null=True, blank=True
    )
    last_port_of_call_name = fields.CharField(max_length=127, null=True, blank=True)
    last_port_of_call_sail_date = models.DateTimeField(blank=True, null=True)
    movement_type = fields.CharField(max_length=127, null=True, blank=True)
    port_name = fields.CharField(max_length=127, null=True, blank=True)
    ihs_port_geo_id = fields.CharField(max_length=127, null=True, blank=True)
    ihs_port_id = fields.CharField(max_length=127, null=True, blank=True)

    latitude = models.DecimalField(
        max_digits=8, decimal_places=6, blank=True, null=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True
    )

    sail_date = models.DateField(blank=True, null=True)
    sail_date_full = models.DateTimeField(blank=True, null=True)
    ship_name = fields.CharField(max_length=127, null=True, blank=True)
    ship_type = fields.CharField(max_length=127, null=True, blank=True)

    creation_date = models.DateTimeField(auto_now=True)
    extra_data = models.TextField(blank=True, null=True)

    objects = ShipMovementManager()

    def __unicode__(self):
        return "IMO: {0} - Ship Name: {1} - Port Name: {2}".format(
            self.imo_id, self.ship_name, self.port_name
        )

    class Meta:
        unique_together = ("imo_id", "timestamp", "ihs_id")
