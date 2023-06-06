from datetime import datetime
import json
from socket import timeout

import pytest
import responses

from screening_api.entities.enums import EntityType
from screening_api.screenings.enums import Severity, Status
from screening_api.ships.enums import ShipAssociateType
from screening_api.ships.models import Ship

from screening_workers.company_sanctions.tasks import (
    ShipCompanyAssociatesCheckTask,
)
from screening_workers.screenings_profiles.models import (
    DefaultScreeningProfile as ScreeningProfile,
)


class TestShipCompanyAssociatesTask:

    task_class = ShipCompanyAssociatesCheckTask

    @pytest.fixture
    def task(self, application):
        return application.tasks[self.task_class.name]

    def test_registered(self, application):
        assert self.task_class.name in application.tasks

    def test_screening_not_found(self, application, factory, task):
        screening_id = 1234567
        task_args = (screening_id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening_id)
        assert screening is None

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening_id)
        assert report is None

    @responses.activate
    @pytest.mark.parametrize('ship_associate_type', [
        ShipAssociateType.GROUP_BENEFICIAL_OWNER,
        ShipAssociateType.OPERATOR,
        ShipAssociateType.REGISTERED_OWNER,
        ShipAssociateType.SHIP_MANAGER,
        ShipAssociateType.TECHNICAL_MANAGER,
    ])
    @pytest.mark.usefixtures('mock_task_run')
    def test_timeout(
            self, mock_task_run, application, factory, task, compliance_client,
            ship_associate_type,
    ):
        mock_task_run.side_effect = timeout
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        sis_company = factory.create_sis_company(name=name)
        company_name_field_name = Ship.get_company_name_field_name(
            ship_associate_type)
        company_field_name = Ship.get_company_field_name(ship_associate_type)
        ship_data = {
            'imo_id': imo_id,
            company_name_field_name: sis_company.name,
            company_field_name: sis_company,
        }
        ship = factory.create_ship(**ship_data)
        screening = factory.create_screening(ship=ship, account_id=account_id)

        response = {
            'results': [],
        }
        responses.add(
            responses.GET,
            '{0}organisation_names/?name={1}'.format(
                compliance_client.base_uri, sis_company.name),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        with pytest.raises(timeout):
            result.get()

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        check_status_field_name = task.check._get_check_status_field_name()
        check_severity_field_name = task.check._get_check_severity_field_name()
        assert screening is not None
        assert screening.account_id == account_id
        assert getattr(screening, check_severity_field_name) ==\
            Severity.UNKNOWN
        assert getattr(screening, check_status_field_name) == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is None

    @responses.activate
    @pytest.mark.parametrize('ship_associate_type', [
        ShipAssociateType.GROUP_BENEFICIAL_OWNER,
        ShipAssociateType.OPERATOR,
        ShipAssociateType.REGISTERED_OWNER,
        ShipAssociateType.SHIP_MANAGER,
        ShipAssociateType.TECHNICAL_MANAGER,
    ])
    def test_no_company(
            self, application, factory, task, compliance_client,
            ship_update_cache, ship_associate_type,
    ):
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        sis_company = factory.create_sis_company(name=name)
        company_name_field_name = Ship.get_company_name_field_name(
            ship_associate_type)
        company_field_name = Ship.get_company_field_name(ship_associate_type)
        ship_data = {
            'imo_id': imo_id,
            company_name_field_name: sis_company.name,
            company_field_name: sis_company,
            'length': 123.4,
            'breadth': 234.5,
            'displacement': 345.6,
            'draught': 456.7,
        }
        ship = factory.create_ship(**ship_data)
        screening = factory.create_screening(ship=ship, account_id=account_id)
        ship_update_cache.put(str(ship.id), datetime.utcnow())

        response = {
            'results': [],
        }
        responses.add(
            responses.GET,
            '{0}organisation_names/?name={1}'.format(
                compliance_client.base_uri, sis_company.name),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        check_status_field_name = task.check._get_check_status_field_name()
        check_severity_field_name = task.check._get_check_severity_field_name()
        assert screening is not None
        assert screening.account_id == account_id
        assert getattr(screening, check_severity_field_name) == Severity.OK
        assert getattr(screening, check_status_field_name) == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        check_report_field_name = task.check._get_check_report_field_name()
        check_report = getattr(report, check_report_field_name)
        assert check_report == {
            'associates': [],
        }

    @responses.activate
    @pytest.mark.parametrize('ship_associate_type', [
        ShipAssociateType.GROUP_BENEFICIAL_OWNER,
        ShipAssociateType.OPERATOR,
        ShipAssociateType.REGISTERED_OWNER,
        ShipAssociateType.SHIP_MANAGER,
        ShipAssociateType.TECHNICAL_MANAGER,
    ])
    def test_no_associates(
            self, application, factory, task, compliance_client,
            ship_update_cache, ship_associate_type,
    ):
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        sis_company = factory.create_sis_company(name=name)
        company_name_field_name = Ship.get_company_name_field_name(
            ship_associate_type)
        company_field_name = Ship.get_company_field_name(ship_associate_type)
        ship_data = {
            'imo_id': imo_id,
            company_name_field_name: sis_company.name,
            company_field_name: sis_company,
        }
        ship = factory.create_ship(**ship_data)
        screening = factory.create_screening(ship=ship, account_id=account_id)
        ship_update_cache.put(str(ship.id), datetime.utcnow())
        compliance_company = factory.create_compliance_entity(
            entity_type=EntityType.ORGANISATION,
            name=sis_company.name, sis=[sis_company, ],
        )

        response = {
            'results': [
                {
                    'id': sis_company.id,
                    'name': sis_company.name,
                    'name_type': "Primary Name",
                    'organisation': {
                        'id': compliance_company.compliance_id,
                        'name': compliance_company.name,
                        'status': 'Active',
                        'organisation_associations': [],
                    },
                }
            ],
        }
        responses.add(
            responses.GET,
            '{0}organisation_names/?name={1}'.format(
                compliance_client.base_uri, sis_company.name),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        check_status_field_name = task.check._get_check_status_field_name()
        check_severity_field_name = task.check._get_check_severity_field_name()
        assert screening is not None
        assert screening.account_id == account_id
        assert getattr(screening, check_severity_field_name) == Severity.OK
        assert getattr(screening, check_status_field_name) == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        check_report_field_name = task.check._get_check_report_field_name()
        check_report = getattr(report, check_report_field_name)
        assert check_report == {
            'associates': [],
        }

    @responses.activate
    @pytest.mark.parametrize('ship_associate_type', [
        ShipAssociateType.GROUP_BENEFICIAL_OWNER,
        ShipAssociateType.OPERATOR,
        ShipAssociateType.REGISTERED_OWNER,
        ShipAssociateType.SHIP_MANAGER,
        ShipAssociateType.TECHNICAL_MANAGER,
    ])
    def test_no_associates_update_associates_no_sanctions(
            self, application, factory, task, compliance_client,
            ship_update_cache, ship_associate_type,
    ):
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        sis_company = factory.create_sis_company(name=name)
        company_name_field_name = Ship.get_company_name_field_name(
            ship_associate_type)
        company_field_name = Ship.get_company_field_name(ship_associate_type)
        ship_data = {
            'imo_id': imo_id,
            company_name_field_name: sis_company.name,
            company_field_name: sis_company,
        }
        ship = factory.create_ship(**ship_data)
        screening = factory.create_screening(ship=ship, account_id=account_id)
        ship_update_cache.put(str(ship.id), datetime.utcnow())
        compliance_company = factory.create_compliance_entity(
            entity_type=EntityType.ORGANISATION,
            name=sis_company.name, sis=[sis_company, ],
        )

        response = {
            'results': [
                {
                    'id': sis_company.id,
                    'name': sis_company.name,
                    'name_type': "Primary Name",
                    'organisation': {
                        'id': compliance_company.compliance_id,
                        'name': compliance_company.name,
                        'status': 'Active',
                        'organisation_associations': [
                            {
                                'id': 123,
                                'status': 'Deleted',
                                'relationship': 'owner',
                                'organisation': {
                                    'id': 2,
                                    'name': 'Company 1',
                                    'status': 'Active',
                                    'organisation_sanctions': [],
                                },
                            },
                        ],
                    },
                }
            ],
        }
        responses.add(
            responses.GET,
            '{0}organisation_names/?name={1}'.format(
                compliance_client.base_uri, sis_company.name),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        check_status_field_name = task.check._get_check_status_field_name()
        check_severity_field_name = task.check._get_check_severity_field_name()
        assert screening is not None
        assert screening.account_id == account_id
        assert getattr(screening, check_severity_field_name) == Severity.OK
        assert getattr(screening, check_status_field_name) == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        check_report_field_name = task.check._get_check_report_field_name()
        check_report = getattr(report, check_report_field_name)
        assert check_report == {
            'associates': [],
        }

    @responses.activate
    @pytest.mark.parametrize('ship_associate_type', [
        ShipAssociateType.GROUP_BENEFICIAL_OWNER,
        ShipAssociateType.OPERATOR,
        ShipAssociateType.REGISTERED_OWNER,
        ShipAssociateType.SHIP_MANAGER,
        ShipAssociateType.TECHNICAL_MANAGER,
    ])
    def test_associates_no_sanctions_update_active_sanction(
            self, application, factory, task, compliance_client,
            ship_update_cache, ship_associate_type,
    ):
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        sis_company = factory.create_sis_company(name=name)
        company_name_field_name = Ship.get_company_name_field_name(
            ship_associate_type)
        company_field_name = Ship.get_company_field_name(ship_associate_type)
        ship_data = {
            'imo_id': imo_id,
            company_name_field_name: sis_company.name,
            company_field_name: sis_company,
        }
        ship = factory.create_ship(**ship_data)
        screening = factory.create_screening(ship=ship, account_id=account_id)
        ship_update_cache.put(str(ship.id), datetime.utcnow())
        compliance_company = factory.create_compliance_entity(
            entity_type=EntityType.ORGANISATION,
            name=sis_company.name, sis=[sis_company, ],
        )

        response = {
            'results': [
                {
                    'id': sis_company.id,
                    'name': sis_company.name,
                    'name_type': "Primary Name",
                    'organisation': {
                        'id': compliance_company.compliance_id,
                        'name': compliance_company.name,
                        'status': 'Active',
                        'organisation_associations': [
                            {
                                'id': 123,
                                'status': 'Deleted',
                                'parent': 1234,
                                'relationship': 'owner',
                                'organisation': {
                                    'id': 2,
                                    'name': 'Company 1',
                                    'status': 'Active',
                                    'organisation_sanctions': [
                                        {
                                            'id': 140001,
                                            'sanction': {
                                                'code': 2,
                                                'name': 'Sanction name',
                                                'status': 'Current',
                                            },
                                            'status': 'ACTIVE',
                                            'since_date': '2001-09-11',
                                            'to_date': None,
                                        }
                                    ],
                                },
                            },
                        ],
                    },
                }
            ],
        }
        responses.add(
            responses.GET,
            '{0}organisation_names/?name={1}'.format(
                compliance_client.base_uri, sis_company.name),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        check_status_field_name = task.check._get_check_status_field_name()
        check_severity_field_name = task.check._get_check_severity_field_name()
        assert screening is not None
        assert screening.account_id == account_id
        assert getattr(screening, check_severity_field_name) ==\
            ScreeningProfile.company_active_sanction_severity
        assert getattr(screening, check_status_field_name) == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        check_report_field_name = task.check._get_check_report_field_name()
        check_report = getattr(report, check_report_field_name)
        assert check_report == {
            'associates': [
                {
                    'company_name': 'Atlantis',
                    'dst_type': 'organisation',
                    'dst_name': 'Company 1',
                    'relationship': 'owner',
                    'sanctions': [
                        {
                            'listed_since': '2001-09-11T00:00:00Z',
                            'listed_to': None,
                            'sanction_name': 'Sanction name',
                            'sanction_severity': 'WARNING',
                        },
                    ],
                },
            ],
        }

    @responses.activate
    @pytest.mark.parametrize('ship_associate_type', [
        ShipAssociateType.GROUP_BENEFICIAL_OWNER,
        ShipAssociateType.OPERATOR,
        ShipAssociateType.REGISTERED_OWNER,
        ShipAssociateType.SHIP_MANAGER,
        ShipAssociateType.TECHNICAL_MANAGER,
    ])
    @pytest.mark.parametrize('entity_type', [
        EntityType.ORGANISATION,
        EntityType.SHIP,
        EntityType.PERSON,
    ])
    def test_associates_sanctions_update_inactive_sanction(
            self, application, factory, task, compliance_client,
            ship_update_cache, ship_associate_type, entity_type,
    ):
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        sis_company = factory.create_sis_company(name=name)
        company_name_field_name = Ship.get_company_name_field_name(
            ship_associate_type)
        company_field_name = Ship.get_company_field_name(ship_associate_type)
        ship_data = {
            'imo_id': imo_id,
            company_name_field_name: sis_company.name,
            company_field_name: sis_company,
        }
        ship = factory.create_ship(**ship_data)
        screening = factory.create_screening(ship=ship, account_id=account_id)
        ship_update_cache.put(str(ship.id), datetime.utcnow())
        compliance_company = factory.create_compliance_entity(
            entity_type=EntityType.ORGANISATION,
            name=sis_company.name, sis=[sis_company, ],
        )
        compliance_entity = factory.create_compliance_entity(
            entity_type=entity_type,
            name='Other company',
        )
        sanction = factory.create_compliance_sanction(
            sanction_list_name='OFAC - WMD Supporters List',
            compliance_entity_ids={
                compliance_entity.id: dict(
                    compliance_id=1,
                    severity=Severity.CRITICAL,
                    start_date='2001-09-11',
                    end_date=None,
                )
            }
        )

        entity_key = entity_type.name.lower()
        entity_sanction_key = entity_key + '_sanctions'
        sanction_name = sanction.sanction_list_name
        response = {
            'results': [
                {
                    'id': sis_company.id,
                    'name': sis_company.name,
                    'name_type': "Primary Name",
                    'organisation': {
                        'id': compliance_company.compliance_id,
                        'name': compliance_company.name,
                        'status': 'Active',
                        'organisation_associations': [
                            {
                                'id': 123,
                                'status': 'Deleted',
                                'parent': 1234,
                                'relationship': 'owner',
                                entity_key: {
                                    'id': compliance_entity.compliance_id,
                                    'name': compliance_entity.name,
                                    'status': 'Active',
                                    entity_sanction_key: [
                                        {
                                            'id': 140001,
                                            'sanction': {
                                                'code':
                                                    sanction.code,
                                                'name':
                                                    sanction_name,
                                                'status': 'Inactive',
                                            },
                                            'status': 'INACTIVE',
                                            'since_date': '2001-09-11',
                                            'to_date': '2002-09-11',
                                        },
                                        {
                                            'id': 140001,
                                            'sanction': {
                                                'code':
                                                    sanction.code,
                                                'name':
                                                    sanction_name,
                                                'status': 'Inactive',
                                            },
                                            'status': 'INACTIVE',
                                            'since_date': '2001-09-11',
                                            'to_date': '2002-09-11',
                                        }
                                    ],
                                },
                            },
                        ],
                    },
                }
            ],
        }
        responses.add(
            responses.GET,
            '{0}organisation_names/?name={1}'.format(
                compliance_client.base_uri, sis_company.name),
            status=200, body=json.dumps(response),
        )
        task_args = (screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        screening = application.screenings_repository.get_or_none(
            id=screening.id)
        check_status_field_name = task.check._get_check_status_field_name()
        check_severity_field_name = task.check._get_check_severity_field_name()
        assert screening is not None
        assert screening.account_id == account_id
        assert getattr(screening, check_severity_field_name) == Severity.OK
        assert getattr(screening, check_status_field_name) == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        check_report_field_name = task.check._get_check_report_field_name()
        check_report = getattr(report, check_report_field_name)
        assert check_report == {
            'associates': [
                {
                    'company_name': 'Atlantis',
                    'dst_type': entity_key,
                    'dst_name': compliance_entity.name,
                    'relationship': 'owner',
                    'sanctions': [
                        {
                            'listed_since': '2001-09-11T00:00:00Z',
                            'listed_to': '2002-09-11T00:00:00Z',
                            'sanction_name': sanction.sanction_list_name,
                            'sanction_severity': 'OK',
                        },
                    ],
                },
            ],
        }
