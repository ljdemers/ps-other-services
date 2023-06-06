import logging

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models

logger = logging.getLogger(__name__)


class ShipDataManualChange(models.Model):
    changed_ship = models.ForeignKey("ShipData", on_delete=models.CASCADE)
    old_data = JSONField()
    new_data = JSONField()
    date_of_change = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    expired = models.BooleanField(default=False)
    reason = models.CharField(max_length=255)
