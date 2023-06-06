import pytest

from screening_api.entities.enums import EntityType
from screening_api.sanctions.repositories import (
    ComplianceEntitySanctionsRepository,
)
from screening_api.screenings.enums import Severity
from screening_api.ships.enums import ShipAssociateType
from screening_api.ships.models import Ship


class TestFindSanctions:

    @pytest.fixture
    def repository(self, session_factory):
        return ComplianceEntitySanctionsRepository(session_factory)

    def test_no_sanctions(self, repository):
        ship_id = 1
        associate_type = ShipAssociateType.OPERATOR

        result = repository.find_sanctions(ship_id, associate_type)

        assert result == []

    def test_sanctions(self, repository, factory):
        imo_id = 1234567
        associate_type = ShipAssociateType.OPERATOR

        sis_company = factory.create_sis_company()
        compliance_company = factory.create_compliance_entity(
            name=sis_company.name, entity_type=EntityType.ORGANISATION,
            sis=[sis_company, ],
        )
        compliance_person = factory.create_compliance_entity(
            name=sis_company.name, entity_type=EntityType.PERSON,
        )
        company_field_name = Ship.get_company_field_name(associate_type)
        ship_data = {
            'imo_id': imo_id,
            company_field_name: sis_company,
        }
        ship = factory.create_ship(**ship_data)
        sanction = factory.create_compliance_sanction(
            sanction_list_name='OFAC - WMD Supporters List',
            compliance_entity_ids={
                compliance_company.id: {
                    'compliance_id': 1,
                    'severity': Severity.WARNING,
                    'start_date': '2001-09-11',
                    'end_date': '2001-09-12',
                },
            },
        )
        factory.create_compliance_sanction(
            sanction_list_name='OFAC2 - WMD Supporters List',
            compliance_entity_ids={
                compliance_person.id: {
                    'compliance_id': 2,
                    'severity': Severity.WARNING,
                    'start_date': '2001-09-11',
                    'end_date': '2001-09-12',
                },
            },
        )

        result = repository.find_sanctions(ship.id, associate_type)

        assert len(result) == 1
        assert result[0].compliance_sanction_id == sanction.id

    def test_sanctions_joinedload_related(self, repository, factory):
        imo_id = 1234567
        associate_type = ShipAssociateType.OPERATOR

        sis_company = factory.create_sis_company()
        compliance_company = factory.create_compliance_entity(
            name=sis_company.name, entity_type=EntityType.ORGANISATION,
            sis=[sis_company, ],
        )
        compliance_person = factory.create_compliance_entity(
            name=sis_company.name, entity_type=EntityType.PERSON,
        )
        company_field_name = Ship.get_company_field_name(associate_type)
        ship_data = {
            'imo_id': imo_id,
            company_field_name: sis_company,
        }
        ship = factory.create_ship(**ship_data)
        sanction = factory.create_compliance_sanction(
            sanction_list_name='OFAC - WMD Supporters List',
            compliance_entity_ids={
                compliance_company.id: {
                    'compliance_id': 1,
                    'severity': Severity.WARNING,
                    'start_date': '2001-09-11',
                    'end_date': '2001-09-12',
                },
            },
        )
        factory.create_compliance_sanction(
            sanction_list_name='OFAC2 - WMD Supporters List',
            compliance_entity_ids={
                compliance_person.id: {
                    'compliance_id': 2,
                    'severity': Severity.WARNING,
                    'start_date': '2001-09-11',
                    'end_date': '2001-09-12',
                },
            },
        )

        result = repository.find_sanctions(
            ship.id, associate_type,
            joinedload_related=['compliance_sanction'],
        )

        assert len(result) == 1
        assert result[0].compliance_sanction_id == sanction.id

    def test_sanctions_multiple(self, repository, factory):
        imo_id = 1234567
        associate_type = ShipAssociateType.OPERATOR

        sis_company = factory.create_sis_company()
        compliance_company = factory.create_compliance_entity(
            name=sis_company.name, entity_type=EntityType.ORGANISATION,
            sis=[sis_company, ],
        )
        compliance_person = factory.create_compliance_entity(
            name=sis_company.name, entity_type=EntityType.PERSON,
        )
        company_field_name = Ship.get_company_field_name(associate_type)
        ship_data = {
            'imo_id': imo_id,
            company_field_name: sis_company,
        }
        ship = factory.create_ship(**ship_data)
        sanction = factory.create_compliance_sanction(
            sanction_list_name='OFAC - WMD Supporters List',
        )
        entity_sanction_1 = factory.create_entity_sanction(
            compliance_entity=compliance_company,
            compliance_sanction=sanction,
            start_date='2001-09-11',
            end_date='2001-09-12',
            severity=Severity.WARNING,
        )
        entity_sanction_2 = factory.create_entity_sanction(
            compliance_entity=compliance_company,
            compliance_sanction=sanction,
            start_date='2011-09-11',
            end_date='2011-09-12',
            severity=Severity.CRITICAL,
        )
        factory.create_compliance_sanction(
            sanction_list_name='OFAC2 - WMD Supporters List',
            compliance_entity_ids={
                compliance_person.id: {
                    'compliance_id': 1,
                    'severity': Severity.WARNING,
                    'start_date': '2001-09-11',
                    'end_date': '2001-09-12',
                },
            },
        )

        result = repository.find_sanctions(
            ship.id, associate_type, sort=['id', ])

        assert len(result) == 2
        assert result[0].compliance_sanction_id == sanction.id
        assert result[0].compliance_entity_id == compliance_company.id
        assert result[0].start_date == entity_sanction_1.start_date
        assert result[0].end_date == entity_sanction_1.end_date
        assert result[1].compliance_sanction_id == sanction.id
        assert result[1].compliance_entity_id == compliance_company.id
        assert result[1].start_date == entity_sanction_2.start_date
        assert result[1].end_date == entity_sanction_2.end_date

    def test_sanctions_blacklisted(self, repository, factory):
        imo_id = 1234567
        associate_type = ShipAssociateType.OPERATOR

        sis_company = factory.create_sis_company()
        compliance_company = factory.create_compliance_entity(
            name=sis_company.name, entity_type=EntityType.ORGANISATION,
            sis=[sis_company, ],
        )
        compliance_person = factory.create_compliance_entity(
            name=sis_company.name, entity_type=EntityType.PERSON,
        )
        company_field_name = Ship.get_company_field_name(associate_type)
        ship_data = {
            'imo_id': imo_id,
            company_field_name: sis_company,
        }
        ship = factory.create_ship(**ship_data)
        sanction = factory.create_compliance_sanction(
            sanction_list_name='OFAC - WMD Supporters List',
            compliance_entity_ids={
                compliance_company.id: {
                    'compliance_id': 1,
                    'severity': Severity.WARNING,
                    'start_date': '2001-09-11',
                    'end_date': '2001-09-12',
                },
            },
        )
        factory.create_compliance_sanction(
            sanction_list_name='OFAC2 - WMD Supporters List',
            compliance_entity_ids={
                compliance_person.id: {
                    'compliance_id': 2,
                    'severity': Severity.WARNING,
                    'start_date': '2001-09-11',
                    'end_date': '2001-09-12',
                },
            },
        )
        blacklisted_sanction = factory.create_compliance_sanction(
            sanction_list_name='World Bank List Other Sanctions',
            compliance_entity_ids={
                compliance_company.id: {
                    'compliance_id': 3,
                    'severity': Severity.WARNING,
                    'start_date': '2001-09-11',
                    'end_date': '2001-09-12',
                },
            },
        )
        blacklisted_sanction_list = factory.create_blacklisted_sanction_list(
            sanction_codes={
                blacklisted_sanction.code: {},
            },
        )

        result = repository.find_sanctions(
            ship.id, associate_type,
            blacklisted_sanction_list_id=blacklisted_sanction_list.id,
        )

        assert len(result) == 1
        assert result[0].compliance_sanction_id == sanction.id
