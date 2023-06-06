import logging

from django.db import models

from ships.models.managers.flag import FlagManager

logger = logging.getLogger(__name__)


class Flag(models.Model):
    code = models.CharField(primary_key=True, max_length=3)
    name = models.CharField(max_length=64, unique=True, db_index=True)
    alt_name = models.CharField(max_length=64, db_index=True, null=True, blank=True)
    world_region = models.CharField(max_length=32)
    world_continent = models.CharField(max_length=16)
    iso_3166_1_alpha_2 = models.CharField(
        max_length=50, null=True, blank=True, db_index=True
    )

    objects = FlagManager()

    def __str__(self):
        return "%s (%s)" % (self.name, self.code)

    def to_dict(self):
        return {
            "code": self.code,
            "name": self.name,
            "alt_name": self.alt_name,
            "iso_3166_1_alpha_2": self.iso_3166_1_alpha_2,
        }
