import pytest

from screening_api.company_associations.repositories import (
    CompanyAssociationsRepository,
)
from screening_api.entities.enums import EntityType
from screening_api.screenings.enums import Severity
from screening_api.ships.enums import ShipAssociateType
from screening_api.ships.models import Ship


class TestFindAssociations:

    @pytest.fixture
    def repository(self, session_factory):
        return CompanyAssociationsRepository(session_factory)

    def test_no_associations(self, repository):
        ship_id = 1
        associate_type = ShipAssociateType.OPERATOR

        result = repository.find_associations(ship_id, associate_type)

        assert result == []

    def test_associations(self, repository, factory):
        imo_id = 1234567
        associate_type = ShipAssociateType.OPERATOR

        sis_company = factory.create_sis_company()
        compliance_company_1 = factory.create_compliance_entity(
            entity_type=EntityType.ORGANISATION,
            name=sis_company.name, sis=[sis_company, ])
        compliance_company_2 = factory.create_compliance_entity(
            entity_type=EntityType.ORGANISATION,
        )
        company_field_name = Ship.get_company_field_name(associate_type)
        ship_data = {
            'imo_id': imo_id,
            company_field_name: sis_company,
        }
        ship = factory.create_ship(**ship_data)
        associations = factory.create_company_association(
            src=compliance_company_1,
            dst=compliance_company_2,
            relationship='Owner',
        )

        result = repository.find_associations(ship.id, associate_type)

        assert len(result) == 1
        assert result[0].id == associations.id


class TestFindAllAssociations:

    @pytest.fixture
    def repository(self, session_factory):
        return CompanyAssociationsRepository(session_factory)

    def test_no_associations(self, repository):
        result = repository.find_all_associations([])

        assert result == []

    def test_ship_no_associations(self, repository, factory):
        imo_id = 1234567

        sis_company = factory.create_sis_company()
        factory.create_compliance_entity(
            entity_type=EntityType.ORGANISATION,
            name=sis_company.name, sis=[sis_company, ])
        ship_data = {
            'imo_id': imo_id,
            'operator_company': sis_company,
        }
        ship = factory.create_ship(**ship_data)

        sis_company_ids = ship.get_company_ids()
        result = repository.find_all_associations(sis_company_ids)

        assert result == []

    def test_associations(self, repository, factory):
        imo_id = 1234567

        sis_company = factory.create_sis_company()
        compliance_company_1 = factory.create_compliance_entity(
            entity_type=EntityType.ORGANISATION,
            name=sis_company.name, sis=[sis_company, ])
        compliance_company_2 = factory.create_compliance_entity(
            entity_type=EntityType.ORGANISATION,
        )
        ship_data = {
            'imo_id': imo_id,
            'operator_company': sis_company,
        }
        ship = factory.create_ship(**ship_data)
        association = factory.create_company_association(
            src=compliance_company_1,
            dst=compliance_company_2,
            relationship='Owner',
        )

        sis_company_ids = ship.get_company_ids()
        result = repository.find_all_associations(sis_company_ids)

        assert len(result) == 1
        assert result[0].id == association.id
        assert result[0].src.id == compliance_company_1.id
        assert result[0].dst.id == compliance_company_2.id

    def test_associations_sanctions(self, repository, factory):
        imo_id = 1234567
        sanction_list_name = 'OFAC - WMD Supporters List'

        sis_company = factory.create_sis_company()
        compliance_company_1 = factory.create_compliance_entity(
            entity_type=EntityType.ORGANISATION,
            name=sis_company.name, sis=[sis_company, ])
        compliance_company_2 = factory.create_compliance_entity(
            entity_type=EntityType.ORGANISATION,
        )
        sanction = factory.create_compliance_sanction(
            sanction_list_name=sanction_list_name,
        )
        entity_sanction = factory.create_entity_sanction(
            compliance_entity=compliance_company_2,
            compliance_sanction=sanction,
            start_date='2001-09-11',
            end_date='2001-09-12',
            severity=Severity.WARNING,
        )
        ship_data = {
            'imo_id': imo_id,
            'operator_company': sis_company,
        }
        ship = factory.create_ship(**ship_data)
        association = factory.create_company_association(
            src=compliance_company_1,
            dst=compliance_company_2,
            relationship='Owner',
        )

        sis_company_ids = ship.get_company_ids()
        result = repository.find_all_associations(
            sis_company_ids,
            joinedload_related=[
                'dst.entity_sanctions',
            ],
            subqueryload=[
                'compliance_sanction',
            ],
        )

        assert len(result) == 1
        assert result[0].id == association.id
        assert result[0].src.id == compliance_company_1.id
        assert result[0].dst.id == compliance_company_2.id
        assert len(result[0].dst.entity_sanctions) == 1
        result_sanction = result[0].dst.entity_sanctions[0]
        assert result_sanction.id == sanction.id
        assert result_sanction.compliance_sanction.id == entity_sanction.id
        assert result_sanction.compliance_sanction.sanction_list_name ==\
            sanction_list_name
