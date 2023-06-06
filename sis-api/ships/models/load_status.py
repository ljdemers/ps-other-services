import logging

from django.db import models
from django.utils.timezone import now

logger = logging.getLogger(__name__)


class LoadStatus(models.Model):
    """
    Contains the load status for an import of a file.
    The status will initially be set to ``LOADING``, proceeding to either
    ``SUCCEEDED`` or ``FAILED``. The load status objects are used to keep
    track of which files have been imported.
    """

    class Meta:
        verbose_name_plural = "LoadStatuses"

    LOADING = "L"
    SUCCEEDED = "S"
    FAILED = "F"
    STATUS = (
        (LOADING, "Loading"),
        (SUCCEEDED, "Load Succeeded"),
        (FAILED, "Load Failed"),
    )

    filename = models.CharField(max_length=255)
    started_date = models.DateTimeField(default=now)
    finished_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS)
    error_traceback = models.TextField(null=True, blank=True)
    load_history = models.ForeignKey(
        "LoadHistory", blank=True, null=True, on_delete=models.CASCADE
    )

    def __unicode__(self):
        return "Run %s [%s] [%s]" % (self.started_date, self.status, self.id)
