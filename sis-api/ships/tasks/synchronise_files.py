import logging
import re
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.utils import timezone

from ships import models
from ships.connectors import Connector, FTPConnector, SFTPConnector
from ships.tasks import import_files
from sis_api.celery import app

logger = logging.getLogger(__name__)


# WARNING: with blocking=False only_one_task_at_a_time will not block, it will
# execute only one task and ignore any new tasks with the same lock name
@app.task(ignore_result=True, soft_time_limit=settings.IMPORT_TIME_LIMIT)
def synchronise_files(import_only=False, exclude_files_re=None):
    load_history = models.LoadHistory.objects.create()
    try:
        do_synchronise_files(
            load_history_id=load_history.id,
            import_only=import_only,
            exclude_files_re=exclude_files_re,
        )
    except Exception as exc:
        load_history = models.LoadHistory.objects.get(id=load_history.id)
        load_history.status = models.LoadHistory.FAILED
        load_history.finished_date = timezone.now()
        load_history.save()
        raise exc

    # if any files failed then set history as failed
    load_statuses = models.LoadStatus.objects.filter(
        load_history_id=load_history.id, status=models.LoadStatus.FAILED
    )

    if load_statuses:
        load_history.status = models.LoadHistory.FAILED

    else:
        load_history.status = models.LoadHistory.SUCCEEDED

    load_history.finished_date = timezone.now()
    load_history.save()


def do_synchronise_files(
    load_history_id: Optional[int] = None,
    import_only: bool = False,
    exclude_files_re: Optional[str] = None,
) -> None:
    """Task for retrieving files from a remote server and depositing them in a
    local directory. Once complete, an import_files task will be invoked."""

    if not import_only:
        if settings.CONNECTOR_TYPE == 'FTP':
            connector = FTPConnector(
                host=settings.OLD_IHS_HOST,
                user=settings.OLD_IHS_USER,
                passwd=settings.OLD_IHS_PASSWORD,
                pasv=settings.OLD_IHS_PASSIVE_MODE,
                work_dir=settings.OLD_IHS_REMOTE_DIR,
            )
            remote_directories = [
                '/',
                settings.OLD_IHS_REMOTE_MOVEMENTS_DIR,
                settings.OLD_IHS_REMOTE_HISTORICAL_DATA_DIR,
            ]
        else:
            connector = SFTPConnector(
                host=settings.IHS_HOST,
                user=settings.IHS_USER,
                passwd=settings.IHS_PASSWORD,
                port=getattr(settings, 'IHS_PORT', 22),
                work_dir=getattr(settings, 'IHS_REMOTE_DIR', '/'),
            )
            remote_directories = [
                '/',
                settings.IHS_REMOTE_MOVEMENTS_DIR,
            ]

        for directory in remote_directories:
            _synchronise_files(
                connector=connector,
                exclude_files_re=exclude_files_re,
                remote_location=directory,
            )

        connector.disconnect()

    import_files(load_history_id=load_history_id)


def _synchronise_files(
    connector: Connector, remote_location: str, exclude_files_re: Optional[str] = None
):
    """Given an connector object and remote_location, synchronise all the files
    in those directories to local server cache."""

    files = connector.list_files(remote_location)

    if exclude_files_re is not None:
        combined_re = '({0})'.format(')|('.join(exclude_files_re))
        logger.info('Exclude files matching: %s', combined_re)
        pattern = re.compile(combined_re)
    else:
        pattern = re.compile('a^')

    remote_path = Path(remote_location)
    for filename in files:
        if pattern.match(filename):
            logger.info('Skipping file on a exclusion list %s', filename)
            continue

        # We always save the file in lowercase, the original FTP files were all
        # lowercase but SFTP use camelcase for the names.
        # We only want to download NEW files so we force everything to lowercase
        # when we check.
        location = Path(settings.IHS_CACHE_DIR) / filename.lower()
        if not location.is_file():
            connector.save_file(str(remote_path / filename), str(location))
