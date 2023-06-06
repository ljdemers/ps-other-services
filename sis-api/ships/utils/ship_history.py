import csv
import datetime as dt
import itertools
import logging
from io import TextIOWrapper
from typing import Dict, Iterator, List, Text, Tuple

from django.db import IntegrityError, transaction

from ships.models import ShipDataHistory
from ships.utils import style, validate_int_field

logger = logging.getLogger(__name__)


SHIP_DATA_HEADERS = {
    'imo_id': 'LRIMOShipNo',
    'ship_name': 'ShipName',
    'ship_status': 'ShipStatus',
    'call_sign': 'CallSign',
    'flag_name': 'FlagName',
    'flag_effective_date': 'FlagEffectiveDate',
    'shiptype_level_5': 'ShiptypeLevel5',
    'registered_owner': 'RegisteredOwner',
    'operator': 'Operator',
    'ship_manager': 'ShipManager',
    'technical_manager': 'TechnicalManager',
    'group_beneficial_owner': 'GroupBeneficialOwner',
    'year_of_build': 'YearOfBuild',
    'registered_owner_code': 'RegisteredOwnerCode',
    'registered_owner_registration_country': 'RegisteredOwnerCountryOfRegistration',
    'registered_owner_control_country': 'RegisteredOwnerCountryOfControl',
    'registered_owner_domicile_country': 'RegisteredOwnerCountryofDomicile',
    'registered_owner_domicile_code': 'RegisteredOwnerCountryofDomicileCode',
    'operator_code': 'OperatorCompanyCode',
    'operator_registration_country': 'OperatorCountryOfRegistration',
    'operator_control_country': 'OperatorCountryOfControl',
    'operator_domicile_country': 'OperatorCountryofDomicileName',
    'operator_domicile_code': 'OperatorCountryofDomicileCode',
    'ship_manager_code': 'ShipManagerCompanyCode',
    'ship_manager_registration_country': 'ShipManagerCountryOfRegistration',
    'ship_manager_control_country': 'ShipManagerCountryOfControl',
    'ship_manager_domicile_country': 'ShipManagerCountryofDomicileName',
    'ship_manager_domicile_code': 'ShipManagerCoutryofDomicileCode',
    'technical_manager_code': 'TechnicalManagerCode',
    'technical_manager_registration_country': 'TechnicalManagerCountryOfRegistration',
    'technical_manager_control_country': 'TechnicalManagerCountryOfControl',
    'technical_manager_domicile_country': 'TechnicalManagerCountryOfControl',
    'technical_manager_domicile_code': 'TechnicalManagerCountryOfDomicileCode',
    'group_beneficial_owner_code': 'GroupBeneficialOwnerCompanyCode',
    'group_beneficial_owner_registration_country': 'GroupBeneficialOwnerCountryOfRegistration',
    'group_beneficial_owner_control_country': 'GroupBeneficialOwnerCountryOfControl',
    'group_beneficial_owner_domicile_country': 'GroupBeneficialOwnerCountryofDomicile',
    'group_beneficial_owner_domicile_code': 'GroupBeneficialOwnerCountryofDomicileCode',
    'mmsi': 'MaritimeMobileServiceIdentityMMSINumber',
}

SHIP_DATA_INT_FIELDS = [
    'year_of_build',
    'registered_owner_code',
    'operator_code',
    'ship_manager_code',
    'technical_manager_code',
    'group_beneficial_owner_code',
]


@transaction.atomic
def import_ship_data_history(
    file_obj: TextIOWrapper, timestamp: dt.datetime, batch_size: int = 100
) -> List[int]:
    """Imports ShipData csv data into ShipDataHistory model."""
    entries = _read_entries(file_obj, timestamp)
    imo_ids2insert = _get_insertion_imo_ids(entries, timestamp)

    ship_history_ids = []
    while True:
        selected_imo_ids = list(itertools.islice(imo_ids2insert, batch_size))
        if not selected_imo_ids:
            break

        try:
            batch = [ShipDataHistory(**entries[imo_id]) for imo_id in selected_imo_ids]
            result = ShipDataHistory.objects.bulk_create(batch, batch_size)
            ship_history_ids += [history.id for history in result]

            logger.info(
                style.SUCCESS(f'Inserted the following IMOs: {selected_imo_ids}.')
            )
        except (ValueError, IntegrityError):
            logger.error(
                style.ERROR(
                    f'Tried to import file {file_obj.name} but failed. '
                    f'Failed to insert the following IMOs: {selected_imo_ids}.'
                )
            )

    logger.info(style.SUCCESS(f'Finished processing file {file_obj.name}.'))

    return ship_history_ids


def _read_entries(file_obj: TextIOWrapper, timestamp: dt.datetime) -> Dict[Text, Dict]:
    """Convert Ship Data row into a valid format.

    Reads Ship Data and translates known headers into valid keys.
    Dict keys should be valid ``ShipDataHistory`` model fields.
    An extra timestamp column is added along with auxiliary data that
    didn't match any key.

    Args:
        file_obj (TextIOWrapper): ship data file object.
        timestamp (datetime): ship data file timestamp.

    Returns:
        dict: imo_id - converted data pairs.
    """
    reader = csv.DictReader(file_obj)

    entries = {}
    for row in reader:
        translated_data, aux_data = _translate_headers(row)

        data = _validate_int_fields(translated_data)
        data.update({'timestamp': timestamp, 'data': aux_data})

        entries[data['imo_id']] = data

    return entries


def _translate_headers(data: Dict) -> Tuple[Dict, Dict]:
    """Translate known Ship Data headers into valid keys.

    Args:
        data: ship data row.

    Returns:
        tuple: translated data, data was untouched.
    """
    copied = data.copy()
    return {
        key: copied.pop(orig_key, None) for key, orig_key in SHIP_DATA_HEADERS.items()
    }, copied


def _validate_int_fields(data: Dict) -> Dict:
    """Check if integer fields are valid.

    Validates specific fields to be numeric fields
    and return their values or an empty string otherwise.

    Args:
        data (dict): ship data row.

    Returns:
        dict: ship data with validated integer fields.
    """
    return {
        key: validate_int_field(value) if key in SHIP_DATA_INT_FIELDS else value
        for key, value in data.items()
    }


def _get_insertion_imo_ids(
    entries: Dict[Text, Dict], timestamp: dt.datetime
) -> Iterator:
    """Get Ship Data IMOs ready for insertion into DB.

    Checks whether ``ShipDataHistory`` records with such IMO
    and timestamp exist in DB and returns those that don't.

    Args:
        entries (dict): ship data history records.
        timestamp (datetime): ship data file timestamp.

    Returns:
        iterator: IMOs iterator. The return value should be
            an iterator, because of how ``itertools.islice``
            function works.
    """
    parsed_imo_ids = entries.keys()
    existing_imo_ids = (
        ShipDataHistory.objects.filter(
            imo_id__in=parsed_imo_ids,
            timestamp=timestamp,
        )
        .values_list('imo_id', flat=True)
        .distinct()
    )

    return (imo_id for imo_id in parsed_imo_ids if imo_id not in existing_imo_ids)
