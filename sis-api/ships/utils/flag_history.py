import itertools
import logging
from operator import itemgetter
from typing import Dict, List, Union

from django.db import transaction
from django.db.models import F, QuerySet

from ships import models
from ships.utils import get_last, str2date, style

logger = logging.getLogger('management')

FLAG_HISTORY_FIELDS = [
    'flag_effective_date',
    'flag_name',
]


def get_ship_history() -> Union[QuerySet, List[models.ShipDataHistory]]:
    """Prepare Ship Data to create Flag History from.

    Returns:
        queryset: ``ships.models.ShipDataHistory`` queryset.
    """
    return (
        models.ShipDataHistory.objects.annotate(ship_history_id=F('id'))
        .values('imo_id', 'timestamp', 'ship_history_id', *FLAG_HISTORY_FIELDS)
        .distinct('imo_id', *FLAG_HISTORY_FIELDS)
        .order_by('imo_id', *FLAG_HISTORY_FIELDS, 'timestamp')
    )


def get_flag_history(
    exclude_manual: bool = False,
) -> Union[QuerySet, List[models.FlagHistory]]:
    """Get flag history records.

    Args:
        exclude_manual (bool): exclude manually added rows.

    Returns:
        queryset: ``ships.models.FlagHistory`` queryset.
    """
    flag_history = models.FlagHistory.objects.values(
        'id', 'timestamp', 'imo_id', *FLAG_HISTORY_FIELDS
    ).order_by('imo_id', 'timestamp')
    if exclude_manual:
        flag_history = flag_history.exclude(manual_edit=True)

    return flag_history


@transaction.atomic
def populate_flag_history(
    ship_history: Union[QuerySet, List[models.ShipDataHistory]], batch_size: int = 100
) -> List[int]:
    """Creates ``FlagHistory`` objects from ``ShipDataHistory`` records.

    Args:
        ship_history (queryset): ``ships.models.ShipDataHistory`` queryset.
        batch_size (int): single DB insert size.

    Returns:
        list: list of created ``ships.models.FlagHistory`` IDs.
    """
    logger.info(f'Populating flag history...')

    # TODO: iterator() accepts chunk_size starting from Django 3.11.1
    ship_history_iter = ship_history.iterator()
    flag_history_ids = []

    num_created = 0
    total_count = ship_history.count()

    while True:
        selected_ship_history = list(itertools.islice(ship_history_iter, batch_size))
        if not selected_ship_history:
            break

        batch = [
            models.FlagHistory(
                flag=models.Flag.objects.find_one(flag_name=ship['flag_name']),
                flag_effective_date=str2date(
                    ship.pop('flag_effective_date'), default=ship['timestamp']
                ),
                **ship,
            )
            for ship in selected_ship_history
        ]
        result = models.FlagHistory.objects.bulk_create(batch, batch_size)
        flag_history_ids += [history.id for history in result]

        num_created += len(batch)
        logger.info('%s/%s done', num_created, total_count)

    logger.info(
        style.SUCCESS('%s flag history records created successfully.'), num_created
    ) if num_created else logger.error(style.ERROR('No flag history records created.'))

    return flag_history_ids


def clean_history(flag_history: Union[QuerySet, List[models.FlagHistory]]) -> List[int]:
    results = []

    for _, group in itertools.groupby(flag_history, itemgetter('imo_id')):
        results.extend(clean_results(group))

    return [flag['id'] for flag in results]


def clean_results(results):
    group_results = []

    for history in results:
        if history['flag_effective_date']:
            previous_result = get_last(group_results)
            if previous_result and should_replace(history, previous_result):
                group_results[-1] = history
                if len(group_results) > 1:
                    group_results = clean_results(group_results)
            else:
                group_results.append(history)

    return group_results


def should_replace(history, prev_history):
    return (
        same_flag_effective_date(history, prev_history)
        or same_flag(history, prev_history)
        or earlier_flag(history, prev_history)
    )


def same_flag(history, prev_history):
    return history['flag_name'] == prev_history['flag_name']


def same_flag_effective_date(history, prev_history):
    return history['flag_effective_date'] == prev_history['flag_effective_date']


def earlier_flag(history, prev_history):
    return history['flag_effective_date'] < prev_history['flag_effective_date']


def mark_ignored_history_records(
    flag_history: Union[QuerySet, List[models.FlagHistory]]
):
    """Mark duplicated and invalid flag history records as ignored.

    Args:
        flag_history (queryset): ``ships.models.FlagHistory`` queryset.
    """
    all_ids = set(flag_history.values_list('id', flat=True))
    valid_ids = set(clean_history(flag_history))
    invalid_ids = list(all_ids - valid_ids)

    num_updated = models.FlagHistory.objects.filter(id__in=invalid_ids).update(
        ignore=True
    )

    logger.warning(
        style.WARNING('%s flag history records marked as ignored.'), num_updated
    )


def dedupe(flag_history: List[Dict], *group_by_attrs: str) -> List[Dict]:
    """Removes duplicates from the formed groups.

    Attrs:
        flag_history (list): flag history records.
        group_by_attr (tuple): attributes to group flag history records by.

    Returns:
        list: flag history records without duplicates.
    """
    return [
        max(group, key=itemgetter('timestamp'))
        for _, group in itertools.groupby(flag_history, itemgetter(*group_by_attrs))
    ]


def remove_invalid_history(flag_history: List[Dict]) -> List[Dict]:
    """Maks records with invalid ``flag_effective_date`` as ignored.

    Outdated records with a higher ``flag_effective_date`` than
    more recent records should be ignored.

    Args:
        flag_history (list): flag history records.

    Returns:
        list: correct flag history records.
    """
    results = []
    for _, group in itertools.groupby(flag_history, itemgetter('imo_id')):
        prev_history = None
        for history in group:
            if (
                not prev_history
                or history['flag_effective_date'] <= prev_history['flag_effective_date']
            ):
                results.append(history)
                prev_history = history

    return results
