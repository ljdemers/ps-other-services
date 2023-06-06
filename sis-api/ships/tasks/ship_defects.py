import logging
import os
import time

from django.conf import settings

from ships import models
from ships.utils.file import import_data_file
from sis_api.celery import app

logger = logging.getLogger(__name__)


@app.task(ignore_result=True, soft_time_limit=settings.IMPORT_TIME_LIMIT)
def import_shipdefects(filename=None, load_history_id=None):
    """Import a shipdefect file from SeaWeb."""
    filename = os.path.abspath(filename)
    logger.info('Processing ship defects file %s', filename)
    if os.path.isfile(filename):
        start_time = time.time()
        num_objs, seen = import_data_file(
            filename, models.ShipDefect, load_history_id=load_history_id
        )

        logger.info(
            '\t\t%s: Imported %s ship defects in %.2f s',
            os.path.basename(filename),
            num_objs,
            time.time() - start_time,
        )
