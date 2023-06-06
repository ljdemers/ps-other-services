from django.test import TestCase
from django.utils import timezone

from ships import models
from ships.models.company_history import CompanyAssociationTypes, CompanyHistory
from ships.tests.factories import (CompanyHistoryFactory, FlagHistoryFactory,
                                   ShipDataHistoryFactory)
from ships.utils import get_first, str2date
from ships.utils.company_history import UNKNOWN_COMPANY_NAME, UNKNOWN_COMPANY_CODE
from ships.utils.file import _update_company_history, _update_flag_history


class TestFlagHistoryNightlyImportUpdate(TestCase):
    def test_no_duplicate_flag_history(self):

        ShipDataHistoryFactory.create(
            imo_id=12345678, flag_name='Panama', flag_effective_date='202201'
        )
        ShipDataHistoryFactory.create(
            imo_id=12345679, flag_name='Panama', flag_effective_date='202201'
        )

        FlagHistoryFactory.create(
            imo_id=12345678, flag_name='Liberia', flag_effective_date=str2date('202101')
        )

        ship_history_ids = models.ShipDataHistory.objects.values_list('id', flat=True)
        _update_flag_history(ship_history_ids)

        assert models.FlagHistory.objects.count() == 3

    def test_exclude_duplicate_flag_history(self):

        ShipDataHistoryFactory.create(
            imo_id=12345678, flag_name='Panama', flag_effective_date='202201'
        )
        ShipDataHistoryFactory.create(
            imo_id=12345679, flag_name='Panama', flag_effective_date='202201'
        )

        FlagHistoryFactory.create(
            imo_id=12345678, flag_name='Panama', flag_effective_date=str2date('202201')
        )

        ship_history_ids = models.ShipDataHistory.objects.values_list('id', flat=True)
        _update_flag_history(ship_history_ids)

        assert models.FlagHistory.objects.count() == 2


class TestCompanyHistoryNightlyImportUpdate(TestCase):
    def test_no_duplicate_company_history(self):
        ship1 = ShipDataHistoryFactory.create(
            imo_id=12345678,
            registered_owner='SeaWalk LLC.',
            registered_owner_code=73312,
            registered_owner_registration_country='Panama',
            registered_owner_control_country='Liberia',
            registered_owner_domicile_country='Panama',
            registered_owner_domicile_code='PAN',
        )
        ship2 = ShipDataHistoryFactory.create(
            imo_id=12345678,
            operator='SeaWalk LLC.',
            operator_code=73312,
            operator_registration_country='Panama',
            operator_control_country='Liberia',
            operator_domicile_country='Panama',
            operator_domicile_code='PAN',
        )

        CompanyHistoryFactory.create(
            imo_id=12345678,
            association_type=CompanyAssociationTypes.SHIP_MANAGER.value,
            company_name='SeaWalk LLC.',
            company_code=73312,
            company_registration_country='Panama',
            company_control_country='Liberia',
            company_domicile_country='Panama',
            company_domicile_code='PAN',
        )

        _update_company_history([ship1.id, ship2.id])
        assert models.CompanyHistory.objects.count() == 11

    def test_exclude_duplicate_company_history(self):
        ship1 = ShipDataHistoryFactory.create(
            imo_id=12345678,
            registered_owner='SeaWalk LLC.',
            registered_owner_code=73312,
            registered_owner_registration_country='Panama',
            registered_owner_control_country='Liberia',
            registered_owner_domicile_country='Panama',
            registered_owner_domicile_code='PAN',
        )
        ship2 = ShipDataHistoryFactory.create(
            imo_id=12345678,
            operator='SeaWalk LLC.',
            operator_code=73312,
            operator_registration_country='Panama',
            operator_control_country='Liberia',
            operator_domicile_country='Panama',
            operator_domicile_code='PAN',
        )

        CompanyHistoryFactory.create(
            imo_id=12345678,
            association_type=CompanyAssociationTypes.OPERATOR.value,
            company_name='SeaWalk LLC.',
            company_code=73312,
            company_registration_country='Panama',
            company_control_country='Liberia',
            company_domicile_country='Panama',
            company_domicile_code='PAN',
        )

        _update_company_history([ship1.id, ship2.id])
        assert models.CompanyHistory.objects.count() == 10

    def test_new_effective_date(self):
        """Test company history nightly update with new company record positive case."""
        effective_date = timezone.now()
        CompanyHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            effective_date=effective_date,
            association_type=CompanyAssociationTypes.OPERATOR.value,
            company_code=73312,
        )

        effective_date = timezone.now()
        CompanyHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            effective_date=effective_date,
            association_type=CompanyAssociationTypes.OPERATOR.value,
            company_code=42341,
        )

        ships = ShipDataHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            operator_code=73312,
        )
        expected_effective_date = get_first(ships).timestamp

        _update_company_history([ship.id for ship in ships])
        assert (
            models.CompanyHistory.objects.filter(
                association_type=CompanyAssociationTypes.OPERATOR.value,
                effective_date=expected_effective_date,
            ).count()
            == 5
        )

    def test_new_effective_date_with_preceding_ignored(self):
        """Test company history nightly update with new company record and preceding ignored positive case."""
        effective_date = timezone.now()
        CompanyHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            effective_date=effective_date,
            association_type=CompanyAssociationTypes.OPERATOR.value,
            company_code=42341,
        )

        effective_date = timezone.now()
        CompanyHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            effective_date=effective_date,
            association_type=CompanyAssociationTypes.OPERATOR.value,
            company_code=73312,
            ignore=True,
        )

        ships = ShipDataHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            operator_code=73312,
        )
        expected_effective_date = get_first(ships).timestamp

        _update_company_history([ship.id for ship in ships])
        assert (
            models.CompanyHistory.objects.filter(
                association_type=CompanyAssociationTypes.OPERATOR.value,
                effective_date=expected_effective_date,
            ).count()
            == 5
        )

    def test_preceding_effective_date(self):
        """Test company history nightly update with preceding company record positive case."""
        effective_date = timezone.now()
        CompanyHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            effective_date=effective_date,
            association_type=CompanyAssociationTypes.OPERATOR.value,
            company_code=71299,
        )

        expected_effective_date = timezone.now()
        CompanyHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            effective_date=expected_effective_date,
            association_type=CompanyAssociationTypes.OPERATOR.value,
            company_code=73312,
        )

        ships = ShipDataHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            operator_code=73312,
        )

        _update_company_history([ship.id for ship in ships])
        assert (
            models.CompanyHistory.objects.filter(
                association_type=CompanyAssociationTypes.OPERATOR.value,
                effective_date=expected_effective_date,
            ).count()
            == 10
        )

    def test_preceding_effective_date_with_preceding_ignored(self):
        """Test company history nightly update with valid preceding company record
        and preceding ignored positive case."""
        expected_effective_date = timezone.now()
        CompanyHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            effective_date=expected_effective_date,
            association_type=CompanyAssociationTypes.OPERATOR.value,
            company_code=73312,
        )

        effective_date = timezone.now()
        CompanyHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            effective_date=effective_date,
            association_type=CompanyAssociationTypes.OPERATOR.value,
            company_code=85858,
            ignore=True,
        )

        ships = ShipDataHistoryFactory.create_batch(
            size=5,
            imo_id=12345678,
            operator_code=73312,
        )

        _update_company_history([ship.id for ship in ships])
        assert (
            models.CompanyHistory.objects.filter(
                association_type=CompanyAssociationTypes.OPERATOR.value,
                effective_date=expected_effective_date,
            ).count()
            == 10
        )

    def test_update_company_ignored(self):
        """Test ignore company history logic on a nightly update positive case."""
        CompanyHistoryFactory.create(
            imo_id=12345678,
            association_type=CompanyAssociationTypes.OPERATOR.value,
            company_code=44357,
        )
        CompanyHistoryFactory.create(
            imo_id=12345678,
            association_type=CompanyAssociationTypes.OPERATOR.value,
            company_code=81233,
        )
        ship = ShipDataHistoryFactory.create(
            imo_id=12345678,
            operator_code=81233,
        )

        _update_company_history([ship.id])
        assert list(
            models.CompanyHistory.objects.filter(
                association_type=CompanyAssociationTypes.OPERATOR.value
            )
            .values_list('ignore', flat=True)
            .order_by('timestamp')
        ) == [False, True, False]

    def test_update_company_manually_ignored(self):
        """Test ignore company history logic on a nightly update for manually ignored record positive case."""
        CompanyHistoryFactory.create(
            imo_id=12345678,
            association_type=CompanyAssociationTypes.OPERATOR.value,
            company_code=44357,
            ignore=True,
        )
        CompanyHistoryFactory.create(
            imo_id=12345678,
            association_type=CompanyAssociationTypes.OPERATOR.value,
            company_code=81233,
        )
        ship = ShipDataHistoryFactory.create(
            imo_id=12345678,
            operator_code=44357,
        )

        _update_company_history([ship.id])
        assert list(
            models.CompanyHistory.objects.filter(
                association_type=CompanyAssociationTypes.OPERATOR.value
            )
            .values_list('ignore', flat=True)
            .order_by('timestamp')
        ) == [True, False, False]

    def test_update_company_blank(self):
        """Test company history nightly update with blank company_name."""
        ship = ShipDataHistoryFactory.create(
            imo_id=12345678,
            operator='',
            operator_code=12345678,
        )

        _update_company_history([ship.id])

        company = CompanyHistory.objects.get(association_type=CompanyAssociationTypes.OPERATOR.value)
        assert company.company_name == UNKNOWN_COMPANY_NAME
        assert company.company_code == UNKNOWN_COMPANY_CODE
