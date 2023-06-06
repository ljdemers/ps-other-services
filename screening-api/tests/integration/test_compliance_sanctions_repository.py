import pytest

from screening_api.entities.enums import EntityType
from screening_api.sanctions.repositories import (
    ComplianceSanctionsRepository,
)
from screening_api.screenings.enums import Severity
from screening_api.ships.enums import ShipAssociateType
from screening_api.ships.models import Ship


class TestFindSanctions:

    @pytest.fixture
    def repository(self, session_factory):
        return ComplianceSanctionsRepository(session_factory)

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
        assert result[0].id == sanction.id

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
            ship.id, associate_type, blacklisted_sanction_list.id)

        assert len(result) == 1
        assert result[0].id == sanction.id
