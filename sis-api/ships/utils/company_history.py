import itertools
import logging
from functools import lru_cache
from operator import itemgetter
from typing import Dict, Generator, List, Union

from django.core.management import color_style
from django.db import connection, transaction
from django.db.models import Case, CharField, F, IntegerField, Q, Value, When
from django.db.models.query import QuerySet

from ships import models
from ships.models.company_history import CompanyAssociationTypes
from ships.utils import get_first

style = color_style()
logger = logging.getLogger('management')

DEFAULT_FIELDS = [
    'ship_history_id',
    'timestamp',
    'imo_id',
]
ASSOCIATION_FIELDS = [
    'company_name',
    'company_code',
    'company_registration_country',
    'company_control_country',
    'company_domicile_country',
    'company_domicile_code',
]

UNKNOWN_COMPANY_NAME = '  Unknown'
UNKNOWN_COMPANY_CODE = 9991001


def get_ship_history() -> Union[QuerySet, List[models.ShipDataHistory]]:
    """Prepare Ship Data to create Company History from.

    Returns:
        queryset: ``ships.models.ShipDataHistory`` queryset.
    """
    company_history_annotations = {}
    company_history_fields = []
    for association_type in CompanyAssociationTypes:
        company_history_annotations.update(get_company_annotation(association_type))
        company_history_fields += map_company_fields(association_type).values()

    ship_history = (
        models.ShipDataHistory.objects.annotate(
            ship_history_id=F('id'), **company_history_annotations
        )
        .values(*company_history_fields, *DEFAULT_FIELDS)
        .order_by('imo_id', 'timestamp')
    )

    return ship_history


def get_company_history(
    association_type: CompanyAssociationTypes, exclude_manual: bool = False
) -> Union[QuerySet, List[models.CompanyHistory]]:
    """Prepares company history records for finding invalid records.

    Queries company history specific fields in specific order so ignore
    mechanism will be able to handle invalid records correctly.

    Args:
        association_type (CompanyAssociationTypes): association type.
        exclude_manual (bool): exclude manually added rows.

    Returns:
        queryset: ``ships.models.CompanyHistory`` queryset.
    """
    history_filters = Q(association_type=association_type.value)
    if exclude_manual:
        history_filters &= Q(manual_edit=False)

    return (
        models.CompanyHistory.objects.values('id', 'imo_id', 'company_code')
        .filter(history_filters)
        .order_by('imo_id', '-timestamp')
    )


@lru_cache()
def map_company_fields(association_type: CompanyAssociationTypes) -> Dict:
    """Maps Ship Data association headers into valid Company History fields.

    Given the field prefix, translate the fields that exist in
    ``ships.models.ShipDataHistory`` into ``ships.models.CompanyHistory`` fields.

    Args:
        association_type (CompanyAssociationTypes): association type.

    Returns:
        dict: translated association headers.
    """
    field_prefix = association_type.name.lower()
    return {
        'company_name': f'{field_prefix}_annotated',
        'company_code': f'{field_prefix}_code_annotated',
        # `company_name` and `company_code` include checks for valid values,
        # so we need to use different names for annotations to avoid same
        # model attributes names
        'company_registration_country': f'{field_prefix}_registration_country',
        'company_control_country': f'{field_prefix}_control_country',
        'company_domicile_country': f'{field_prefix}_domicile_country',
        'company_domicile_code': f'{field_prefix}_domicile_code',
    }


def get_company_annotation(association_type: CompanyAssociationTypes) -> Dict:
    """Annotates `company_name` and `company_code` with values checks.

    `company_name` receives '  Unknown' value
        if `company_name` for specific `association_type` is blank.
    `company_code` receives '9991001' value
        if `company_name` for specific `association_type` is '  Unknown'.

    Args:
        association_type (CompanyAssociationTypes): association type.

    Returns:
        dict: company history annotations.
    """
    field_prefix = association_type.name.lower()

    company_name = field_prefix
    company_code = f'{field_prefix}_code'

    annotated_company_name = f'{company_name}_annotated'
    annotated_company_code = f'{company_code}_annotated'

    return {
        annotated_company_name: Case(
            When(**{company_name: ''}, then=Value(UNKNOWN_COMPANY_NAME, CharField())),
            default=F(company_name),
        ),
        annotated_company_code: Case(
            When(
                **{annotated_company_name: UNKNOWN_COMPANY_NAME},
                then=Value(UNKNOWN_COMPANY_CODE, IntegerField()),
            ),
            default=F(company_code),
        ),
    }


def normalize_ship_history_data(
    association_type: CompanyAssociationTypes,
    ship_history: Union[QuerySet, List[models.ShipDataHistory]],
    is_update: bool,
) -> List[Dict]:
    """Normalize ship history data before insertion.

    Remove duplicates and translate ship history headers of
    specific association type into headers suitable for insertion.

    Args:
        association_type (CompanyAssociationTypes): association type.
        ship_history (queryset): ship history records.
        is_update (bool): update indicator, which specifies if company data
            is loaded from scratch or is just updated.

    Returns:
        list: ship history records ready for insertion.
    """
    unique_ships = _dedupe_ship_history(association_type, ship_history)
    company_data = _map_ship_history(association_type, unique_ships)
    enriched_company_data = _enrich_ship_history(
        association_type, company_data, is_update
    )

    return enriched_company_data


def _dedupe_ship_history(
    association_type: CompanyAssociationTypes,
    ship_history: Union[QuerySet, List[models.ShipDataHistory]],
) -> List[Dict]:
    """Removes redundant ship history.

    Args:
        association_type (CompanyAssociationTypes): association type.
        ship_history (queryset): ship history records.

    Returns:
        list: unique ship history records.
    """
    return [
        get_first(group)
        for _, group in itertools.groupby(
            ship_history,
            itemgetter('imo_id', *map_company_fields(association_type).values()),
        )
    ]


def _map_ship_history(
    association_type: CompanyAssociationTypes, ship_history: List[Dict]
) -> List[Dict]:
    """Maps ship history fields.

    Maps fields from ship data into fields suitable
    for company history insertions.

    Args:
        association_type (CompanyAssociationTypes): association type.
        ship_history (list): ship history records.

    Returns:
        list: data suitable for company history insertions.
    """
    return [
        _translate_association_fields(association_type, ship) for ship in ship_history
    ]


def _enrich_ship_history(
    association_type: CompanyAssociationTypes,
    ship_history: List[Dict],
    is_update: bool = False,
) -> List[Dict]:
    """Adds additional information to the ship data.

    Creates ``effective_date`` value based on the earliest ``timestamp``
    of the ship for specific company. If ``is_update`` is set to ``True``,
    meaning that company history population is done during a nightly update,
    then ``effective_date`` will be set based on the previous company data
    if such company precedes the inserted one.

    Args:
        association_type (CompanyAssociationTypes): association type.
        ship_history (list): ship history records.
        is_update (bool): update indicator, which specifies if company data
            is loaded from scratch or is just updated.

    Returns:
        list: data with ``effective_date`` field.
    """
    result = []

    for (imo_id, company_code), group in itertools.groupby(
        ship_history, itemgetter('imo_id', 'company_code')
    ):
        companies = list(group)
        effective_date = min([company['timestamp'] for company in companies])

        if is_update:
            prev_company = (
                models.CompanyHistory.objects.filter(
                    association_type=association_type.value, imo_id=imo_id, ignore=False
                )
                .order_by('-timestamp')
                .first()
            )
            if prev_company and prev_company.company_code == company_code:
                effective_date = prev_company.effective_date

        for company in companies:
            company['effective_date'] = effective_date
            result.append(company)

    return result


def _translate_association_fields(
    association_type: CompanyAssociationTypes, ship: Dict
) -> Dict:
    """Translate ship history record headers.

    Retrieve values with appropriate headers for
    company history insertions.

    Args:
        association_type (CompanyAssociationTypes): association type.
        ship (dict): ship history record.

    Returns:
        dict: data with correct headers.
    """
    result = {
        'association_type': association_type.value,
    }

    result.update({field: ship[field] for field in DEFAULT_FIELDS})
    result.update(
        {
            new_field: ship[old_field]
            for new_field, old_field in map_company_fields(association_type).items()
        }
    )

    return result


@transaction.atomic
def populate_company_history(
    association_type: CompanyAssociationTypes,
    ship_history: Union[QuerySet, List[models.ShipDataHistory]],
    is_update: bool = False,
):
    """Creates company history from ship data history.

    Args:
        association_type (CompanyAssociationTypes): association type.
        ship_history (queryset): ``ships.models.ShipDataHistory`` queryset.
        is_update (bool): update indicator, which specifies if company data
            is loaded from scratch or is just updated.

    Returns:
        list: list of created ``ships.models.CompanyHistory`` IDs.
    """
    data = normalize_ship_history_data(association_type, ship_history, is_update)
    result = models.CompanyHistory.objects.bulk_create(
        [models.CompanyHistory(**company) for company in data]
    )

    return [company.id for company in result]


@transaction.atomic
def mark_ignored_history_records(
    company_history: Union[QuerySet, List[models.CompanyHistory]],
    batch_size: int = 100,
) -> int:
    """Mark duplicated and invalid company history records as ignored.

    Args:
        batch_size (int): single UPDATE query size.
        company_history (queryset): ``ships.models.CompanyHistory`` queryset.

    Returns:
        int: number of ignored records.
    """
    invalid_ids = _clean_history(company_history)

    num_updated = 0
    while True:
        batch = list(itertools.islice(invalid_ids, batch_size))
        if not batch:
            break

        with connection.cursor() as cursor:
            cursor.execute(
                'UPDATE ships_companyhistory SET ignore=true WHERE id=ANY((%s))',
                [batch],
            )
        num_updated += len(batch)

    return num_updated


def _clean_history(
    company_history: Union[QuerySet, List[models.CompanyHistory]]
) -> Generator:
    """Finds invalid company history records.

    Groups company history records by ``imo_id`` and ``company_code``
    and returns ID for each record except the first (most recent) in
    the group. The first record is the most recent because ordering is
    preserved in ``get_company history`` method.

    Args:
        company_history (queryset): ``ships.models.CompanyHistory`` queryset.

    Returns:
        generator: generator object with invalid company history IDs.
            It's important to return iterotor/generator because it's
            used with ``islice`` then.
    """
    for _, group in itertools.groupby(
        company_history, itemgetter('imo_id', 'company_code')
    ):
        next(group)  # skip the most recent record as it is valid
        for company in group:
            yield company['id']
