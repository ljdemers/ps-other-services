import itertools
import logging
import os
import time
import zipfile
from contextlib import contextmanager
from io import TextIOBase
from random import randrange

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone
from django.utils.timezone import now

from ships import models
from ships.tasks.globavista import globavista_ship_export
from ships.tasks.ship_info import import_shipinfo
from ships.tasks.ship_inspections import import_shipinspections
from sis_api.celery import app

logger = logging.getLogger(__name__)


@app.task(ignore_result=True, soft_time_limit=settings.IMPORT_TIME_LIMIT)
def import_files(load_history_id=None):
    """
    Look through contents of the downloaded archive files, see if any of them
    have not been imported, and send any CSV files to the correct import
    function.
    """
    cache_dir = settings.IHS_CACHE_DIR

    filenames = sorted(os.listdir(cache_dir))
    for filename in filenames:
        source = os.path.join(cache_dir, filename)
        if not os.path.isfile(source):
            continue

        if not source.endswith('.zip'):
            continue

        try:
            archive = zipfile.ZipFile(source, 'r')
        except Exception:
            logger.error("Failed to unzip %s", source, exc_info=1)
            continue

        for filename in archive.namelist():
            if not filename.lower().endswith('.csv'):
                continue

            if (
                'ShipData' not in filename
                and 'Inspections' not in filename
                and 'MovementData' not in filename
            ):
                continue

            if models.LoadStatus.objects.exclude(
                status=models.LoadStatus.FAILED
            ).filter(filename=filename):
                continue

            archive.extract(filename, cache_dir)
            destination = os.path.abspath(os.path.join(cache_dir, filename))
            if 'ShipData' in filename:
                import_shipinfo(destination, load_history_id=load_history_id)
            elif 'Inspections' in filename:
                import_shipinspections(destination, load_history_id=load_history_id)

            elif 'MovementData' in filename:
                import_movement_history(destination, load_history_id=load_history_id)

        archive.close()

    if settings.GLOBAVISTA_EXPORT_ENABLED:
        logger.info('Scheduling Globavista export')
        globavista_ship_export.delay()
    else:
        logger.info('Skipping Globavista export as it is disabled')


def import_movement_history(filename, load_history_id):
    """Import ship movement data file from SeaWeb."""
    filename = os.path.abspath(filename)
    logger.info('Processing ship movement history file %s', filename)
    if os.path.isfile(filename):
        start_time = time.time()

        load_history = models.LoadHistory.objects.get(id=load_history_id)
        # Update the db to indicate load status
        load_status = models.LoadStatus.objects.create(
            filename=os.path.basename(filename),
            status=models.LoadStatus.LOADING,
            load_history=load_history,
        )

        table_name = 'ships_shipmovement'
        with create_temp_table(table_name) as tmp_table:
            # Cleaning up input files as we read them:
            # replace wrong lat, replace x0
            # byte char, add creation_date at the end
            with IterStringIO(
                append_data(
                    replace_data(
                        replace_data(
                            open(filename, 'r', encoding='utf-8'), '971.616666700', ''
                        ),
                        chr(0),
                        '',
                    ),
                    f',{now().isoformat()}',
                )
            ) as file_obj:
                sql_query = (
                    f'COPY {tmp_table} '
                    f'(imo_id, arrival_date, timestamp, ihs_id, country_name, '
                    f'ihs_creation_date, destination_port, '
                    f'estimated_time_of_arrival, hours_in_port, '
                    f'last_port_of_call_arrival_date, '
                    f'last_port_of_call_code, last_port_of_call_country, '
                    f'last_port_of_call_country_code, last_port_of_call_name, '
                    f'last_port_of_call_sail_date, movement_type, port_name, '
                    f'ihs_port_geo_id, ihs_port_id, latitude, longitude, '
                    f'sail_date, sail_date_full, ship_name, ship_type, creation_date) '
                    f'FROM STDIN WITH DELIMITER \',\' CSV HEADER'
                )

                logger.info('Starting import of the data into the temp table')

                try:
                    _run_sql_copy_query(sql_query, file_obj)
                except Exception as err:
                    load_status.status = models.LoadStatus.FAILED
                    load_status.finished_date = timezone.now()
                    load_status.save()
                    raise err

                logger.info(
                    "Merge the temp table into the main table, ignoring positions "
                    "that are already in the ships_shipmovement table."
                )

                # Change this query to be a join with the main_table as select 1 from main table is slower,
                # as the table has more rows
                merge_tables_command = (
                    f'INSERT INTO {table_name} '
                    f'(imo_id, arrival_date, timestamp, ihs_id, country_name, '
                    f'ihs_creation_date, destination_port, estimated_time_of_arrival, '
                    f'hours_in_port, last_port_of_call_arrival_date, '
                    f'last_port_of_call_code, last_port_of_call_country, '
                    f'last_port_of_call_country_code, last_port_of_call_name, '
                    f'last_port_of_call_sail_date, movement_type, port_name, '
                    f'ihs_port_geo_id, ihs_port_id, latitude, longitude, sail_date, '
                    f'sail_date_full, ship_name, ship_type, creation_date) '
                    f'(SELECT imo_id, arrival_date, timestamp, ihs_id, country_name, '
                    f'ihs_creation_date, destination_port, estimated_time_of_arrival, '
                    f'hours_in_port, last_port_of_call_arrival_date, '
                    f'last_port_of_call_code, last_port_of_call_country, '
                    f'last_port_of_call_country_code, last_port_of_call_name, '
                    f'last_port_of_call_sail_date, movement_type, port_name, '
                    f'ihs_port_geo_id, ihs_port_id, latitude, longitude, sail_date, '
                    f'sail_date_full, ship_name, ship_type, creation_date '
                    f'FROM {tmp_table} '
                    f'WHERE NOT EXISTS ('
                    f'SELECT 1 FROM ships_shipmovement '
                    f'WHERE ships_shipmovement.ihs_id={tmp_table}.ihs_id '
                    f'AND ships_shipmovement.imo_id={tmp_table}.imo_id '
                    f'AND ships_shipmovement.timestamp={tmp_table}.timestamp'
                    f'));'
                )
                try:
                    with transaction.atomic():
                        cursor = connection.cursor()
                        cursor.execute(merge_tables_command)
                except Exception as err:
                    load_status.status = models.LoadStatus.FAILED
                    load_status.finished_date = timezone.now()
                    load_status.error_traceback = str(err)
                    load_status.save()
                    raise err

                logger.info(f'TRUNCATING `%s` table', tmp_table)

    # Everything went as expected, clean it all up
    os.unlink(filename)
    load_status.status = models.LoadStatus.SUCCEEDED
    load_status.finished_date = timezone.now()
    load_status.save()


class IterStringIO(TextIOBase):
    def __init__(self, iterable=None):
        iterable = iterable or []
        self.iter = itertools.chain.from_iterable(iterable)

    def not_newline(self, s):
        return s not in {'\n', '\r', '\r\n'}

    def write(self, iterable):
        to_chain = itertools.chain.from_iterable(iterable)
        self.iter = itertools.chain.from_iterable([self.iter, to_chain])

    def read(self, n=None):
        if n is None:
            return ''.join(list(self.iter))
        return ''.join(list(itertools.islice(self.iter, n)))

    def readline(self, n=None):
        to_read = itertools.takewhile(self.not_newline, self.iter)
        if n is None:
            return ''.join(list(to_read))
        return ''.join(list(itertools.islice(to_read, n)))


def stream_filter(filter):
    def stream(iostream, *args, **kwargs):
        return filter(iostream, *args, **kwargs)

    return stream


@stream_filter
def append_data(stream, data):
    for line in stream:
        yield f'{line.rstrip()}{data}\n'


@stream_filter
def replace_data(stream, needle, replace):
    for line in stream:
        yield line.replace(needle, replace)


@stream_filter
def str_to_byte(stream):
    for line in stream:
        yield bytearray(line, 'utf-8')


@contextmanager
def create_temp_table(main_table_name, drop_column='id'):
    """Create tmp table based on main table"""
    rand = randrange(100000)
    new_table_name = f'tmp_{main_table_name}_{rand}'
    cursor = connection.cursor()
    query = f'CREATE TEMP TABLE {new_table_name}(like {main_table_name} EXCLUDING CONSTRAINTS)'
    cursor.execute(query)
    query = f"ALTER TABLE {new_table_name} DROP COLUMN {drop_column};"
    cursor.execute(query)
    yield new_table_name
    # Temp table should be only till the end of db session
    # but we can clean up now
    query = f'DROP TABLE {new_table_name}'
    cursor.execute(query)


def _run_sql_copy_query(sql_query, file_obj):
    # We need to the Postgresql cursor. Best way I could find to get it
    # See the following for me details:
    # https://pythonhosted.org/psycopg2/cursor.html#cursor.copy_expert
    with transaction.atomic():
        postgres_cursor = connection.cursor()
        postgres_cursor.copy_expert(sql_query, file_obj)
