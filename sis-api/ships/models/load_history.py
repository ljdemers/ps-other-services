import logging

from django.db import models
from django.utils.timezone import now

logger = logging.getLogger(__name__)


class LoadHistory(models.Model):
    class Meta:
        verbose_name_plural = "LoadHistory"

    LOADING = "L"
    SUCCEEDED = "S"
    FAILED = "F"
    STATUS = (
        (LOADING, "Loading"),
        (SUCCEEDED, "Load Succeeded"),
        (FAILED, "Load Failed"),
    )
    started_date = models.DateTimeField(default=now)
    finished_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS, default=LOADING)
