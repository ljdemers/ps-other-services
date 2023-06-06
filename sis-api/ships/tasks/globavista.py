import logging

from celery.exceptions import Retry
from django.conf import settings
from django.utils.timezone import now

from ships.export import export_file_for_globavista, sync_to_s3
from sis_api.celery import app

logger = logging.getLogger(__name__)


@app.task(
    ignore_result=True,
    soft_time_limit=settings.IMPORT_TIME_LIMIT,
    retry_kwargs={'max_retries': 5, 'countdown': 5},
)
def globavista_ship_export():
    target_filename = now().strftime(settings.GLOBAVISTA_EXPORT_FILE_PATTERN)
    logger.info('Exporting globavista ships report to %s', target_filename)
    exported_file = export_file_for_globavista(target_filename, True)
    logger.info('Exported report')
    if not (
        exported_file
        and sync_to_s3(
            exported_file,
            settings.GLOBAVISTA_EXPORT_S3_BUCKET,
            settings.GLOBAVISTA_EXPORT_S3_KEY_PREFIX,
        )
    ):
        logger.warning('Export sync to S3 failed')
        raise Retry()
    logger.info('Export sync to S3 successful')
