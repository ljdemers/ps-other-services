import logging

from django.db import models
from django.db.models import Q

logger = logging.getLogger(__name__)


class FlagManager(models.Manager):
    def find_one(self, flag_name=None):
        """Find the flag of this name."""
        if not flag_name:
            return

        flag_name = flag_name.lower()
        try:
            return self.model.objects.get(
                Q(name__iexact=flag_name) | Q(alt_name__iexact=flag_name)
            )
        except self.model.DoesNotExist:
            return None
