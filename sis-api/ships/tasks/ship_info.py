import logging
import os
import time

from django.conf import settings

from ships import models
from ships.utils.file import import_data_file
from sis_api.celery import app

logger = logging.getLogger(__name__)


@app.task(ignore_result=True, soft_time_limit=settings.IMPORT_TIME_LIMIT)
def import_shipinfo(filename=None, load_history_id=None):
    """Import a shipinfo file from SeaWeb"""
    filename = os.path.abspath(filename)
    logger.info('Processing ship info file %s', filename)
    seen = []
    if os.path.isfile(filename):
        start_time = time.time()
        num_objs, seen = import_data_file(
            filename, models.ShipData, load_history_id=load_history_id
        )
        logger.info(
            '\t\t%s: Imported %s ships in %.2f s',
            os.path.basename(filename),
            num_objs,
            time.time() - start_time,
        )
    #  After importing update the imported objects with the manual changes
    apply_manual_changes_on_ship_data(seen)


def apply_manual_changes_on_ship_data(imos_seen):
    # Get all the changes
    changes = models.ShipDataManualChange.objects.filter(
        expired=False, changed_ship__imo_id__in=imos_seen
    )
    # Iterate through them
    for change in changes.iterator():
        # Get the ShipData objects that have been manually changed
        ship_data_entry = models.ShipData.objects.get(imo_id=change.changed_ship.imo_id)

        # Check if all the fields of change object were not matched in source
        # object
        expire_change = []
        # Check if data has changed, to know if we should store original data
        data_changed = False
        original_data = ship_data_entry.data.copy()
        # Iterate through changed fields
        for changed_key, old_value in change.old_data.items():
            # Check if in the object in the DB the value of the key is same as
            # in the one that was checked (for example somebody changed manually
            # flag from USA to CAN, then source changed it to ITA, we don't want
            # to change ITA to CAN.
            if old_value == getattr(ship_data_entry, changed_key):
                # Set the new value in object if everything matched
                # Set it also to the data dict inside the object
                setattr(ship_data_entry, changed_key, change.new_data[changed_key])
                ship_data_entry.data[changed_key] = change.new_data[changed_key]
                data_changed = True
                expire_change.append(False)
            else:
                expire_change.append(True)
        if all(expire_change) is True:
            change.expired = True
        if data_changed is True:
            ship_data_entry.original_data = original_data
        change.save()
        # Save the ship data entry if everything went fine
        ship_data_entry.save()
