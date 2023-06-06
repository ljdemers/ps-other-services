import django.contrib.admin.views.main

from ships.admin.company_history import CompanyHistoryAdmin
from ships.admin.flag_history import FlagHistoryAdmin
from ships.admin.load_history import LoadHistoryAdmin
from ships.admin.load_status import LoadStatusAdmin
from ships.admin.mmsi_history import MMSIHistoryAdmin
from ships.admin.ship_data import ShipDataAdmin
from ships.admin.ship_data_manual_change import ShipDataManualChangeAdmin
from ships.admin.ship_inspection import ShipInspectionAdmin
from ships.admin.ship_movement import ShipMovementAdmin

# Tweak of the standard admin functionality to show nulls as an empty string.
django.contrib.admin.views.main.EMPTY_CHANGELIST_VALUE = ""


__all__ = [
    "CompanyHistoryAdmin",
    "FlagHistoryAdmin",
    "LoadHistoryAdmin",
    "LoadStatusAdmin",
    "MMSIHistoryAdmin",
    "ShipDataAdmin",
    "ShipDataManualChangeAdmin",
    "ShipInspectionAdmin",
    "ShipMovementAdmin",
]
