import logging

from django.db import models
from django.db.models import fields

from ships.constants import IMO_MAX_LEN

logger = logging.getLogger(__name__)


class FlagHistory(models.Model):
    class Meta:
        verbose_name = "flag_history"
        verbose_name_plural = "flag history"

    imo_id = fields.CharField(max_length=IMO_MAX_LEN, db_index=True)
    flag_name = fields.CharField(max_length=255, db_index=True)
    flag_effective_date = fields.DateTimeField()
    timestamp = fields.DateTimeField()
    manual_edit = fields.BooleanField(default=False)
    ignore = fields.BooleanField(default=False, db_index=True)

    flag = models.ForeignKey("Flag", null=True, blank=True, on_delete=models.SET_NULL)
    ship_history = models.ForeignKey(
        "ShipDataHistory",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="flag_history",
    )
