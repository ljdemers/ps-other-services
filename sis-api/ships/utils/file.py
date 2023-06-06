import csv
import logging
import os
from typing import List, Tuple, Union

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from ships import models, seaweb
from ships.models.company_history import CompanyAssociationTypes
from ships.utils import convert_file_timestamp, str2date
from ships.utils.company_history import ASSOCIATION_FIELDS, get_company_history
from ships.utils.company_history import \
    get_ship_history as get_ship4company_history
from ships.utils.company_history import map_company_fields
from ships.utils.company_history import \
    mark_ignored_history_records as ignore_company_duplicates
from ships.utils.company_history import populate_company_history
from ships.utils.flag_history import FLAG_HISTORY_FIELDS, get_flag_history
from ships.utils.flag_history import get_ship_history as get_ship4flag_history
from ships.utils.flag_history import \
    mark_ignored_history_records as ignore_flag_duplicates
from ships.utils.flag_history import populate_flag_history
from ships.utils.ship_history import import_ship_data_history

logger = logging.getLogger(__name__)


@transaction.atomic
def import_file(input_file, model, ignore_seen_pk=True):
    """Import objects from an open file."""
    num_objs = 0
    fields = [field.name for field in model._meta.fields if field.name != 'id']

    pkname = model._meta.pk.name
    if pkname not in fields:
        pkname = fields[0]

    # TODO: Refactor Whole with DictReader
    reader = csv.reader((line.replace('\0', '') for line in input_file), delimiter=",")

    col_names = [seaweb.translate(col) for col in next(reader)]
    # Merge together all repeated pks
    seen = []
    for row in reader:
        datum = dict(
            [
                (field, value.strip())
                for (field, value) in zip(col_names, row)
                if value.strip()
            ]
        )

        pk = datum.get(pkname)
        if not pk or (ignore_seen_pk and pk in seen):
            logger.error("ignoring %s", datum)
            continue

        attrs = {}
        for field in fields:
            attrs[field] = datum.get(field, None)

        if num_objs % 1000 == 0:
            logger.info("Loaded %s (%s)", num_objs, model)

        # attrs is a dict with model fields unlike datum
        model.objects.import_data(attrs=attrs, data=datum)
        seen.append(pk)
        num_objs += 1

    logger.info("Loaded a total of %s (%s)", num_objs, model)
    return num_objs, seen


def import_data_file(filename, model, load_history_id=None, ignore_seen_pk=True):
    """
    Import a downloaded file from SeaWeb, and report the success status in a
    LoadStatus object.
    """
    logger.info('Importing data file %s...', filename)
    load_history = models.LoadHistory.objects.get(id=load_history_id)
    # Update the db to indicate load status
    load = models.LoadStatus.objects.create(
        filename=os.path.basename(filename),
        status=models.LoadStatus.LOADING,
        load_history=load_history,
    )

    try:
        with open(filename, encoding='utf-8', errors='backslashreplace') as fh:
            num_objs, seen = import_file(fh, model, ignore_seen_pk)
            fh.seek(0)
            ship_history_ids = import_ship_data_history(
                fh, convert_file_timestamp(fh.name)
            )

        _update_flag_history(ship_history_ids)
        _update_company_history(ship_history_ids)

        load_status = models.LoadStatus.objects.get(id=load.id)
        load_status.status = models.LoadStatus.SUCCEEDED
        load_status.finished_date = timezone.now()
        load_status.save()

        # We don't update ImportHistory here as it will be updated on the end
        # of the import.
        return num_objs, seen
    except Exception as main_exception:
        try:
            load_status = models.LoadStatus.objects.get(id=load.id)
            load_status.status = models.LoadStatus.FAILED
            load_status.finished_date = timezone.now()
            load_status.save()
        except Exception:
            pass

        raise main_exception


def _update_flag_history(ship_history_ids: List[int]):
    """Update flag history from a newly inserted ship history data.

    Args:
        ship_history_ids (list): inserted ship history records IDs.
    """
    ship_history = get_ship4flag_history().filter(id__in=ship_history_ids)

    ship_history, prev_flag_history_ids = _filter_flag_history_changed(ship_history)
    curr_flag_history_ids = populate_flag_history(ship_history)

    flag_history_ids = prev_flag_history_ids + curr_flag_history_ids
    if flag_history_ids:
        flag_history = get_flag_history().filter(id__in=flag_history_ids)
        ignore_flag_duplicates(flag_history)


def _update_company_history(ship_history_ids: List[int]):
    """Update company history from a newly inserted ship history data.

    Args:
        ship_history_ids (list): inserted ship history records IDs.
    """
    ship_history = get_ship4company_history().filter(id__in=ship_history_ids)
    for association_type in CompanyAssociationTypes:
        (
            ship_history_changed,
            prev_company_history_ids,
        ) = _filter_company_history_changed(association_type, ship_history)
        curr_company_history_ids = populate_company_history(
            association_type, ship_history_changed, is_update=True
        )

        company_history_ids = prev_company_history_ids + curr_company_history_ids
        if company_history_ids:
            company_history = get_company_history(association_type).filter(
                id__in=company_history_ids
            )
            ignore_company_duplicates(company_history)


def _filter_flag_history_changed(
    ship_history: Union[QuerySet, List[models.ShipDataHistory]]
) -> Tuple[Union[QuerySet, List[models.ShipDataHistory]], List[int],]:
    """Determine which ``ShipDataHistory`` will be used to create a new ``FlagHistory`` record.

    If ``flag`` and ``flag_effective_date`` fields duplicate
    row for specific IMO within most recent flag history record,
    then such ship data will be excluded from the insertion into
    a flag history.

    Args:
        ship_history (queryset): new ship data history records.
        which were just inserted from a night file update.

    Returns:
        tuple: ship history that have a different ``flag`` or
            ``flag_effective_date`` for that IMO, preceding
            flag history records to the ship data history that
            is going to be inserted.
    """
    imo_ids = ship_history.values_list('imo_id', flat=True)

    prev_flag_history = (
        models.FlagHistory.objects.filter(imo_id__in=imo_ids)
        .distinct('imo_id')
        .order_by('imo_id', '-timestamp')
    )
    prev_flag_history_ids = prev_flag_history.values_list('id', flat=True)
    prev_flag_history = {
        flag['imo_id']: flag
        for flag in prev_flag_history.values('id', 'imo_id', *FLAG_HISTORY_FIELDS)
    }

    excluded_ships = []
    excluded_flags = []
    for ship in ship_history.iterator():
        flag = prev_flag_history.get(ship['imo_id'])
        if (
            flag
            and ship['flag_name'] == flag['flag_name']
            and str2date(ship['flag_effective_date']) == flag['flag_effective_date']
        ):
            excluded_ships.append(ship['ship_history_id'])
            excluded_flags.append(flag['id'])

    return ship_history.exclude(id__in=excluded_ships), list(
        prev_flag_history_ids.exclude(id__in=excluded_flags)
    )


def _filter_company_history_changed(
    association_type: CompanyAssociationTypes,
    ship_history: Union[QuerySet, List[models.ShipDataHistory]],
) -> Tuple[Union[QuerySet, List[models.ShipDataHistory]], List[int],]:
    """Determine which ``ShipDataHistory`` will be used to create a new ``CompanyHistory`` record.

    If all company fields duplicate row for specific IMO within
    most recent company history record, then such ship data will
    be excluded from the insertion into a company history.

    Args:
        ship_history (queryset): new ship data history records.
        which were just inserted from a night file update.

    Returns:
        tuple: ship history that have a different company
            attributes for that IMO, preceding company
            history records to the ship data history that
            is going to be inserted.
    """
    imo_ids = {ship['imo_id'] for ship in ship_history}

    prev_company_history = (
        models.CompanyHistory.objects.filter(
            imo_id__in=imo_ids, association_type=association_type.value
        )
        .distinct(
            'imo_id',
        )
        .order_by('imo_id', '-timestamp')
    )
    prev_company_history_ids = prev_company_history.values_list('id', flat=True)
    prev_company_history = {
        company['imo_id']: company
        for company in prev_company_history.values('id', 'imo_id', *ASSOCIATION_FIELDS)
    }

    excluded_ships = []
    excluded_companies = []
    for ship in ship_history.iterator():
        company = prev_company_history.get(ship['imo_id'])
        if company and all(
            [
                ship[old_field] == company[new_field]
                for new_field, old_field in map_company_fields(association_type).items()
            ]
        ):
            excluded_ships.append(ship['ship_history_id'])
            excluded_companies.append(company['id'])

    return ship_history.exclude(id__in=excluded_ships), list(
        prev_company_history_ids.exclude(id__in=excluded_companies)
    )
