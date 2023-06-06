import string
from datetime import date, datetime
from functools import partial
from random import randrange

import factory
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timezone import make_aware
from factory.fuzzy import (FuzzyChoice, FuzzyDateTime, FuzzyDecimal,
                           FuzzyInteger, FuzzyText)
from faker import Faker
from faker.providers import date_time

from ships import models
from ships.constants import IMO_MAX_LEN, YEAR_MONTH_FORMAT
from ships.models.company_history import CompanyAssociationTypes
from ships.utils import get_first

MIN_FLAG_EFFECTIVE_DATE = make_aware(datetime(1765, 5, 7))

SHIPS = [
    'MONTKAJ',
    'ABU AL ABYAD',
    'LEGACY V',
    'AL FAHEDI',
    'ALL SEVEN',
    'VA BENE',
    'ARCARIUS',
    'TIZIANA',
    'ATLANTIC GOOSE',
    'CHESELLA',
]
SHIP_STATUSES = [
    'In Service/Commission',
    'Converting/Rebuilding',
    'In Casualty/or repairing',
    'Laid Up',
]
SHIP_TYPES = [
    'Accommodation Platform, jack up',
    'Accommodation Platform, semi submersible',
    'Accommodation Ship',
    'Accommodation Vessel, Stationary',
    'Aggregates Carrier',
    'Aircraft Carrier',
    'Air Cushion Vehicle Passenger',
    'Air Cushion Vehicle Passenger/Ro-Ro (Vehicles)',
    'Air Cushion Vehicle Patrol Vessel',
    'Air Cushion Vehicle, work vessel',
    'Alcohol Tanker',
    'Anchor Handling Tug Supply',
    'Anchor Handling Vessel',
    'Articulated Pusher Tug',
    'Asphalt/Bitumen Tanker',
]


def _get_country_code(obj, attribute):
    return get_first(
        [
            country['alpha-3-code']
            for country in date_time.Provider.countries
            if country['name'] == getattr(obj, attribute, None)
        ]
    )


def _random_flag_effective_date():
    flag_effective_date = Faker().date_between(MIN_FLAG_EFFECTIVE_DATE)
    return flag_effective_date.strftime(YEAR_MONTH_FORMAT)


def _random_year_of_build(obj):
    flag_effective_date = datetime.strptime(obj.flag_effective_date, YEAR_MONTH_FORMAT)
    return flag_effective_date.year - randrange(30)


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'user-{0}'.format(n))
    email = factory.Sequence(lambda n: 'user-{0}@polestarglobal.com'.format(n))
    first_name = 'User'
    last_name = factory.Sequence(lambda n: '{0}'.format(n))

    class Meta:
        model = User

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return

        self.set_password(extracted or 'letmein')  # Default password 'letmein'.


class FlagModelFactory(factory.django.DjangoModelFactory):
    code = 'ZWE'
    name = 'Zimbabwe'
    alt_name = None
    world_region = 'Eastern Africa'
    world_continent = 'Africa'
    iso_3166_1_alpha_2 = 'ZW'

    class Meta:
        model = models.Flag


class ShipDataFactory(factory.django.DjangoModelFactory):
    imo_id = FuzzyInteger(low=100000000, high=9999999999)
    mmsi = FuzzyInteger(low=100000000, high=999999999)
    ship_name = FuzzyText()
    shiptype_level_5 = FuzzyText()
    call_sign = FuzzyText()

    flag = factory.SubFactory(FlagModelFactory)
    flag_name = 'Zimbabwe'

    port_of_registry = 'Maputo'
    ship_status = 'In Service/Commission'

    gross_tonnage = FuzzyInteger(low=100000000, high=9999999999)
    length_overall_loa = FuzzyInteger(low=100, high=999)
    year_of_build = FuzzyInteger(low=1900, high=2019)

    registered_owner = 'Denver Maritime Ltd'
    operator = 'Pasifik Gemi Isletmeciligi'
    ship_manager = 'Pasifik Gemi Isletmeciligi'
    technical_manager = 'Pasifik Gemi Isletmeciligi'
    group_beneficial_owner = 'Kiran Holding AS'

    data = {'immah_random_data_key': 'Imma value'}
    updated = datetime.now()

    class Meta:
        model = models.ShipData


class ShipDataHistoryFactory(factory.django.DjangoModelFactory):

    timestamp = factory.LazyFunction(timezone.now)

    imo_id = FuzzyText(length=IMO_MAX_LEN, chars=string.digits)
    mmsi = FuzzyText(length=10, chars=string.digits)
    ship_name = FuzzyChoice(SHIPS)
    shiptype_level_5 = FuzzyChoice(SHIP_TYPES)
    call_sign = FuzzyText(length=5, chars=string.ascii_uppercase)

    flag_name = factory.Faker('country')
    flag_effective_date = factory.LazyFunction(_random_flag_effective_date)

    port_of_registry = factory.Faker('country')
    ship_status = FuzzyChoice(SHIP_STATUSES)

    gross_tonnage = FuzzyDecimal(900, 200000)
    length_overall_loa = FuzzyInteger(low=100, high=999)
    year_of_build = factory.LazyAttribute(_random_year_of_build)

    registered_owner = factory.Faker('company')
    registered_owner_code = FuzzyInteger(9999999)
    registered_owner_registration_country = factory.Faker('country')
    registered_owner_control_country = factory.Faker('country')
    registered_owner_domicile_country = factory.Faker('country')
    registered_owner_domicile_code = factory.LazyAttribute(
        partial(_get_country_code, attribute='registered_owner_domicile_country')
    )

    operator = factory.Faker('company')
    operator_code = FuzzyInteger(9999999)
    operator_registration_country = factory.Faker('country')
    operator_control_country = factory.Faker('country')
    operator_domicile_country = factory.Faker('country')
    operator_domicile_code = factory.LazyAttribute(
        partial(_get_country_code, attribute='operator_domicile_country')
    )

    ship_manager = factory.Faker('company')
    ship_manager_code = FuzzyInteger(9999999)
    ship_manager_registration_country = factory.Faker('country')
    ship_manager_control_country = factory.Faker('country')
    ship_manager_domicile_country = factory.Faker('country')
    ship_manager_domicile_code = factory.LazyAttribute(
        partial(_get_country_code, attribute='ship_manager_domicile_country')
    )

    technical_manager = factory.Faker('company')
    technical_manager_code = FuzzyInteger(9999999)
    technical_manager_registration_country = factory.Faker('country')
    technical_manager_control_country = factory.Faker('country')
    technical_manager_domicile_country = factory.Faker('country')
    technical_manager_domicile_code = factory.LazyAttribute(
        partial(_get_country_code, attribute='technical_manager_domicile_country')
    )

    group_beneficial_owner = factory.Faker('company')
    group_beneficial_owner_code = FuzzyInteger(9999999)
    group_beneficial_owner_registration_country = factory.Faker('country')
    group_beneficial_owner_control_country = factory.Faker('country')
    group_beneficial_owner_domicile_country = factory.Faker('country')
    group_beneficial_owner_domicile_code = factory.LazyAttribute(
        partial(_get_country_code, attribute='group_beneficial_owner_domicile_country')
    )

    data = {'random': 'data'}

    class Meta:
        model = models.ShipDataHistory


class ShipDataManualChangeFactory(factory.django.DjangoModelFactory):
    changed_ship = factory.SubFactory(ShipDataFactory)
    old_data = {'registered_owner': 'Denver Maritime Ltd'}
    new_data = {'registered_owner': 'Scrooge Inc.'}
    date_of_change = datetime.now()
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = models.ShipDataManualChange


class ShipInspectionFactory(factory.django.DjangoModelFactory):
    inspection_id = FuzzyText(length=50, chars=string.digits)
    imo_id = factory.Sequence(lambda n: '9{0:06}'.format(n))
    authorisation = FuzzyChoice(['Tokyo MOU', 'Paris MOU', 'US Coastguard'])
    ship_name = factory.Sequence(lambda n: 'Ship-{0}'.format(n))
    call_sign = FuzzyText(length=5, chars=string.ascii_uppercase)
    flag_name = 'Liberia'
    shipclass = FuzzyChoice(
        [
            "Lloyd's Register",
            'American Bureau of Shipping (ABS)',
            'Det Norske Veritas (DNVC)',
            'Registro Italiano Navale',
            'Russian Maritime Register of Shipping',
        ]
    )
    shiptype = FuzzyChoice(
        [
            'Comercial yacht',
            'Oil tanker',
            'Offshore service vessel',
            'Tank Ship',
            'Freight Ship',
            'Ro-Ro Passenger Ship',
            'Bulk carrier',
            'General cargo/multi-purpose',
        ]
    )
    expanded_inspection = FuzzyChoice([True, False])
    inspection_date = str(date.today())
    date_release = str(date.today())
    no_days_detained = FuzzyInteger(low=0, high=5)
    port_name = 'Algeciras'
    country_name = 'Spain'
    owner = 'Pole Star Space Applications Ltd.'
    manager = 'Simon Morris'
    charterer = 'Lanny Day'
    cargo = 'Beer'
    detained = FuzzyChoice([True, False])
    no_defects = FuzzyInteger(low=0, high=10)
    source = FuzzyChoice(['Tokyo MOU', 'Paris MOU', 'US Coastguard'])
    gt = FuzzyInteger(low=900, high=25000)
    dwt = FuzzyInteger(low=0, high=150000)
    yob = FuzzyInteger(low=1970, high=2019)
    other_inspection_type = FuzzyChoice(['Initial inspection', 'Detail inspection'])
    number_part_days_detained = FuzzyDecimal(low=0, high=50, precision=2)

    class Meta:
        model = models.ShipInspection


class ShipDefectFactory(factory.django.DjangoModelFactory):
    defect_id = FuzzyInteger(low=1)
    inspection = factory.SubFactory(ShipInspectionFactory)
    defect_text = factory.Sequence(lambda n: f'Text for ShipDefect-{n}')
    defect_code = FuzzyText(length=10)
    action_1 = factory.Sequence(lambda n: f'Action 1 for ShipDefect-{n}')
    action_2 = factory.Sequence(lambda n: f'Action 2 for ShipDefect-{n}')
    action_3 = factory.Sequence(lambda n: f'Action 3 for ShipDefect-{n}')
    other_action = FuzzyText(length=180)
    recognised_org_resp_yn = FuzzyText(length=10)
    recognised_org_resp_code = FuzzyText(length=10)
    recognised_org_resp = FuzzyText(length=50)
    other_recognised_org_resp = FuzzyText(length=10)
    main_defect_code = FuzzyText(length=10)
    main_defect_text = FuzzyText(length=180)
    action_code_1 = FuzzyText(length=10)
    action_code_2 = FuzzyText(length=10)
    action_code_3 = FuzzyText(length=10)
    class_is_responsible = FuzzyText(length=10)
    detention_reason_deficiency = FuzzyText(length=10)

    class Meta:
        model = models.ShipDefect


class FlagFactory(factory.django.DjangoModelFactory):
    code = FuzzyText(length=3)
    name = FuzzyText(length=20)
    alt_name = FuzzyText(length=25)
    world_region = FuzzyText(length=32)
    world_continent = FuzzyText(length=16)
    iso_3166_1_alpha_2 = FuzzyText(length=2)

    class Meta:
        model = models.Flag
        django_get_or_create = ['code']


class FlagHistoryFactory(factory.django.DjangoModelFactory):
    timestamp = factory.LazyFunction(timezone.now)
    imo_id = FuzzyText(length=IMO_MAX_LEN, chars=string.digits)

    flag_name = FuzzyText(length=20)
    flag = factory.SubFactory(FlagFactory, name=flag_name)
    flag_effective_date = FuzzyDateTime(MIN_FLAG_EFFECTIVE_DATE)

    manual_edit = FuzzyChoice([True, False])
    ignore = FuzzyChoice([True, False])

    class Meta:
        model = models.FlagHistory


class CompanyHistoryFactory(factory.django.DjangoModelFactory):
    timestamp = factory.LazyFunction(timezone.now)
    effective_date = factory.LazyAttribute(lambda obj: obj.timestamp)
    imo_id = FuzzyText(length=IMO_MAX_LEN, chars=string.digits)
    association_type = FuzzyChoice([choice.value for choice in CompanyAssociationTypes])
    company_name = FuzzyText(length=20)
    company_code = FuzzyInteger(9999999)
    company_registration_country = FuzzyText(length=15)
    company_control_country = FuzzyText(length=32)
    company_domicile_country = FuzzyText(length=25)
    company_domicile_code = FuzzyText(length=3)

    manual_edit = FuzzyChoice([True, False])
    ignore = False

    ship_history = factory.SubFactory(ShipDataHistoryFactory)

    class Meta:
        model = models.CompanyHistory
