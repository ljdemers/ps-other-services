from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from tastypie.models import ApiKey

from ships.models.company_history import CompanyHistory
from ships.models.flag import Flag
from ships.models.flag_history import FlagHistory
from ships.models.load_history import LoadHistory
from ships.models.load_status import LoadStatus
from ships.models.mmsi_history import MMSIHistory
from ships.models.ship_data import ShipData
from ships.models.ship_data_history import ShipDataHistory
from ships.models.ship_data_manual_change import ShipDataManualChange
from ships.models.ship_defect import ShipDefect
from ships.models.ship_image import ShipImage
from ships.models.ship_inspection import ShipInspection
from ships.models.ship_movement import ShipMovement


def create_api_key(sender, **kwargs):
    """
    A signal for hooking up automatic ``ApiKey`` creation. Overrides the
    standard tastypie hook to ensure a timezone-aware creation time.
    """
    if kwargs.get("created") is True:
        ApiKey.objects.create(user=kwargs.get("instance"), created=timezone.now())


models.signals.post_save.connect(create_api_key, sender=User)

__all__ = [
    "CompanyHistory",
    "Flag",
    "FlagHistory",
    "LoadHistory",
    "LoadStatus",
    "MMSIHistory",
    "ShipData",
    "ShipDataHistory",
    "ShipDataManualChange",
    "ShipDefect",
    "ShipImage",
    "ShipInspection",
    "ShipMovement",
]
