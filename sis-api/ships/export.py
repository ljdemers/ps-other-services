import logging
import lzma
from pathlib import Path
from typing import Optional

from boto import connect_s3
from boto.exception import AWSConnectionError, BotoClientError, S3CopyError
from boto.s3.bucket import Key

from django.db import connection, Error as DBError

logger = logging.getLogger(__name__)
SQL_FILE = 'ships/sql/extract_ships.sql'


def file_size(filepath: str) -> int:
    """
    Inspect the size of a file.

    Missing files are reported as 0 size.

    Args:
        filepath: path to file we're inspecting

    Returns:
        size of the file in bytes
    """
    try:
        return Path(filepath).stat().st_size
    except FileNotFoundError:
        return 0


def export_file_for_globavista(
        target_filename: str,
        lzma_compressed: bool = False
) -> Optional[str]:
    """
    Export shipdata in globavista's expected export format.

    Args:
        target_filename: Target file path
        lzma_compressed: Flat for lzma compression of file

    Returns:
        exported filename if successful, otherwise None
    """
    if lzma_compressed:
        target_filename = f'{target_filename}.xz'
        file_open = lzma.open
    else:
        file_open = open

    try:
        file_content = Path(SQL_FILE).read_text()
    except FileNotFoundError:
        logger.error('Unable to export as sql file (%s) is missing', SQL_FILE)
        return None

    copy_command = f'COPY ({file_content}) TO STDOUT WITH CSV HEADER'

    try:
        with connection.cursor() as cur, file_open(target_filename, 'w') as f:
            logger.info('Exporting ship data to %s', target_filename)
            cur.copy_expert(copy_command, f)
    except FileNotFoundError as e:
        logger.error(
            'Unable to export as target file (%s) is invalid: %s',
            target_filename,
            e
        )
        return None
    except DBError as e:
        logger.error('Unable to export due to database error: %s', e)
        return None

    if not file_size(target_filename):
        logger.error('Ship data export "succeeded" but target file is empty')
        return None
    return target_filename


def sync_to_s3(file_path: str, bucket: str, key_prefix: str = '') -> bool:
    """
    Sync a file to an aws s3 bucket.

    Args:
        file_path: the path to the source file
        bucket: the name of the target bucket.
        key_prefix: a prefix to apply to the s3 key (file path).

    Returns:
        bool: Whether process was successful (uploaded or was not needed)
    """
    if not bucket:
        logger.info('No bucket configured so not uploading')
        return True

    try:
        file = Path(file_path)
        key = Key(connect_s3().get_bucket(bucket))
        key.key = f'{key_prefix}{file.name}'
        key.set_contents_from_filename(file_path)
    except (
        AWSConnectionError, BotoClientError, S3CopyError, FileNotFoundError
    ) as e:
        logger.error(
            'Unable to copy "%s"to s3 bucket "%s": %s',
            file_path,
            bucket,
            e
        )
        return False

    logger.info('Uploaded %s to %s', file_path, bucket)
    file.unlink()
    logger.info('Deleted local file %s', file_path)
    return True
