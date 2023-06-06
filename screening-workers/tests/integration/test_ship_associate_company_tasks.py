from datetime import datetime
import json
from socket import timeout

import pytest
import responses

from screening_api.entities.enums import EntityType
from screening_api.screenings.enums import Severity, Status
from screening_api.ships.models import Ship

from screening_workers.company_sanctions.tasks import (
    ShipRegisteredOwnerCompanyCheckTask, ShipOperatorCompanyCheckTask,
    ShipBeneficialOwnerCompanyCheckTask, ShipManagerCompanyCheckTask,
    ShipTechnicalManagerCompanyCheckTask,
)
from screening_workers.screenings_profiles.models import (
    DefaultScreeningProfile as ScreeningProfile,
)


class BaseTestAssociateCompanyTask:

    task_class = NotImplemented

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

    @pytest.mark.usefixtures('mock_task_run')
    def test_timeout(self, mock_task_run, application, factory, task):
        mock_task_run.side_effect = timeout
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        ship_associate_type = task.check.associate_type
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
    def test_no_sanctions(
            self, application, factory, task, compliance_client,
            ship_update_cache):
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        ship_associate_type = task.check.associate_type
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
            'company_name': name,
            'sanctions': [],
        }

    @responses.activate
    def test_no_sanctions_ship_company_name_update(
            self, application, factory, task, compliance_client, sis_client):
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        name_new = 'Atlantis 2'
        ship_associate_type = task.check.associate_type
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
            'objects': [
                {
                    "breadth": "32.200",
                    "call_sign": "3EUO6",
                    "classification_society": "Nippon Kaiji Kyokai 1983-09",
                    "country_of_build": "Japan",
                    "deadweight": "16149",
                    "depth": "19.560",
                    "displacement": "0",
                    "doc_company": "Unknown",
                    "document_of_compliance_doc_company_code": "9991001",
                    "draught": "9.417",
                    "flag": {
                        "alt_name": None,
                        "code": "PAN",
                        "iso_3166_1_alpha_2": "PA",
                        "name": "Panama"
                    },
                    "flag_effective_date": "198309",
                    "flag_name": "Panama",
                    "gross_tonnage": "43684",
                    "group_beneficial_owner": name_new,
                    "group_beneficial_owner_company_code": "5231178",
                    "group_beneficial_owner_country_of_control": "Japan",
                    "group_beneficial_owner_country_of_domicile": "Japan",
                    "group_beneficial_owner_country_of_domicile_code": "JPN",
                    "group_beneficial_owner_country_of_registration": "Japan",
                    "image": None,
                    "imo_id": str(imo_id),
                    "length_overall_loa": "183.532",
                    "mmsi": "",
                    "operator": name_new,
                    "operator_company_code": "0153911",
                    "operator_country_of_control": "Japan",
                    "operator_country_of_domicile_code": "JPN",
                    "operator_country_of_domicile_name": "Japan",
                    "operator_country_of_registration": "Japan",
                    "pandi_club": "Unknown",
                    "port_of_registry": "Panama",
                    "registered_owner": name_new,
                    "registered_owner_code": "5188328",
                    "registered_owner_country_of_control": "Japan",
                    "registered_owner_country_of_domicile": "Japan",
                    "registered_owner_country_of_domicile_code": "JPN",
                    "registered_owner_country_of_registration": "Japan",
                    "resource_uri": "/api/v1/ships/8300418",
                    "safety_management_certificate_date_issued": "20090408",
                    "safety_management_certificate_doc_company": "Unknown",
                    "ship_manager": name_new,
                    "ship_manager_company_code": "0979251",
                    "ship_manager_country_of_control": "Japan",
                    "ship_manager_country_of_domicile_code": "JPN",
                    "ship_manager_country_of_domicile_name": "Japan",
                    "ship_manager_country_of_registration": "Japan",
                    "ship_name": "OCEAN ACE",
                    "ship_status": "Broken Up",
                    "shipbuilder": "Imabari Shbldg - Marugame",
                    "shiptype_level_5": "Vehicles Carrier",
                    "shiptype_level_5_hull_type":
                        "Ship Shape Including Multi-Hulls",
                    "speed": "18.00",
                    "stat_code_5": "A35B2RV",
                    "technical_manager": name_new,
                    "technical_manager_code": "0979251",
                    "technical_manager_country_of_control": "Japan",
                    "technical_manager_country_of_domicile": "Japan",
                    "technical_manager_country_of_domicile_code": "JPN",
                    "technical_manager_country_of_registration": "Japan",
                    "thumbnail": None,
                    "year_of_build": "1983"
                }
            ],
        }
        responses.add(
            responses.GET,
            '{0}ships/?imo_id={1}'.format(sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
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
            'company_name': name_new,
            'sanctions': [],
        }

    def test_no_sanctions_no_update(
            self, application, factory, task, ship_update_cache):
        imo_id = 12345
        account_id = 123456
        ship = factory.create_ship(imo_id=imo_id)
        screening = factory.create_screening(ship=ship, account_id=account_id)
        ship_update_cache.put(str(ship.id), datetime.utcnow())

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
            'company_name': None,
            'sanctions': [],
        }

    @responses.activate
    def test_no_sanctions_update_sanctions(
            self, application, factory, task, compliance_client,
            ship_update_cache):
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        ship_associate_type = task.check.associate_type
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

        response = {
            'results': [
                {
                    'id': sis_company.id,
                    'name': sis_company.name,
                    'name_type': "Primary Name",
                    'organisation': {
                        'id': sis_company.id,
                        'name': sis_company.name,
                        'status': 'Active',
                        'organisation_sanctions': [
                            {
                                'id': 140001,
                                'sanction': {
                                    'code': 2,
                                    'name': 'Sanction List name',
                                    'status': 'Current',
                                },
                                'status': 'ACTIVE',
                                'since_date': '2012-07-12',
                                'to_date': None,
                            }
                        ]
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
            'company_name': name,
            'sanctions': [
                {
                    'listed_since': '2012-07-12T00:00:00Z',
                    'listed_to': None,
                    'sanction_name': 'Sanction List name',
                    'sanction_severity': 'WARNING',
                }
            ],
        }

    def test_sanction_inactive_no_update(
            self, application, factory, task, company_sanctions_update_cache,
            ship_update_cache):
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        ship_associate_type = task.check.associate_type
        sis_company = factory.create_sis_company(name=name)
        company_field_name = Ship.get_company_field_name(ship_associate_type)
        ship_data = {
            'imo_id': imo_id,
            company_field_name: sis_company,
        }
        ship = factory.create_ship(**ship_data)
        screening = factory.create_screening(ship=ship, account_id=account_id)
        ship_update_cache.put(str(ship.id), datetime.utcnow())
        cache_key = str(sis_company.id)
        company_sanctions_update_cache.put(cache_key, datetime.utcnow())
        compliance_company = factory.create_compliance_entity(
            entity_type=EntityType.ORGANISATION,
            name=sis_company.name, sis=[sis_company, ])
        factory.create_compliance_sanction(
            sanction_list_name='OFAC - WMD Supporters List',
            compliance_entity_ids={
                compliance_company.id: {
                    'compliance_id': 1,
                    'severity': Severity.CRITICAL,
                    'start_date': '2001-09-11',
                    'end_date': '2001-09-12',
                },
            },
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
            'company_name': name,
            'sanctions': [
                {
                    'sanction_name': 'OFAC - WMD Supporters List',
                    'listed_since': '2001-09-11T00:00:00Z',
                    'listed_to': '2001-09-12T00:00:00Z',
                    'sanction_severity': 'OK',
                },
            ],
        }

    @responses.activate
    def test_sanction_inactive_update_sanction(
            self, application, factory, task, compliance_client,
            ship_update_cache):
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        ship_associate_type = task.check.associate_type
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
            name=sis_company.name, sis=[sis_company, ])
        sanction = factory.create_compliance_sanction(
            sanction_list_name='OFAC - WMD Supporters List',
            compliance_entity_ids={
                compliance_company.id: {
                    'compliance_id': 140001,
                    'severity': Severity.CRITICAL,
                    'start_date': '2001-09-11',
                    'end_date': '2001-09-12',
                },
            },
        )

        response = {
            'results': [
                {
                    'id': sis_company.id,
                    'name': sis_company.name,
                    'name_type': 'Primary Name',
                    'organisation': {
                        'id': compliance_company.compliance_id,
                        'name': compliance_company.name,
                        'status': "Active",
                        'organisation_sanctions': [
                            {
                                'id': 140001,
                                'sanction': {
                                    'code': sanction.code,
                                    'name': sanction.sanction_list_name,
                                    'status': 'Current',
                                },
                                'status': 'INACTIVE',
                                'since_date': '2001-09-11',
                                'to_date': '2001-09-12',
                            },
                            {
                                'id': 140002,
                                'sanction': {
                                    'code': sanction.code + 1,
                                    'name': 'Sanction List name',
                                    'status': 'Current',
                                },
                                'status': 'ACTIVE',
                                'since_date': '2012-07-12',
                                'to_date': None,
                            }
                        ],
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
        assert getattr(screening, check_severity_field_name) ==\
            ScreeningProfile.company_active_sanction_severity
        assert getattr(screening, check_status_field_name) == Status.DONE

        report = application.screenings_reports_repository.get_or_none(
            screening_id=screening.id)
        assert report is not None
        check_report_field_name = task.check._get_check_report_field_name()
        check_report = getattr(report, check_report_field_name)
        assert check_report == {
            'company_name': name,
            'sanctions': [
                {
                    'sanction_name': 'OFAC - WMD Supporters List',
                    'listed_since': '2001-09-11T00:00:00Z',
                    'listed_to': '2001-09-12T00:00:00Z',
                    'sanction_severity': 'OK',
                },
                {
                    'listed_since': '2012-07-12T00:00:00Z',
                    'listed_to': None,
                    'sanction_name': 'Sanction List name',
                    'sanction_severity': 'WARNING',
                }
            ],
        }

    @responses.activate
    def test_sanction_inactive_update_no_sanction(
            self, application, factory, task, compliance_client,
            ship_update_cache):
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        ship_associate_type = task.check.associate_type
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
            name=sis_company.name, sis=[sis_company, ])
        factory.create_compliance_sanction(
            sanction_list_name='OFAC - WMD Supporters List',
            compliance_entity_ids={
                compliance_company.id: {
                    'compliance_id': 140001,
                    'severity': Severity.CRITICAL,
                    'start_date': '2001-09-11',
                    'end_date': '2001-09-12',
                },
            },
        )

        response = {
            'results': [
                {
                    'id': sis_company.id,
                    'name': sis_company.name,
                    'name_type': 'Primary Name',
                    'organisation': {
                        'id': compliance_company.compliance_id,
                        'name': compliance_company.name,
                        'status': "Active",
                        'organisation_sanctions': [
                        ]
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
            'company_name': name,
            'sanctions': [],
        }

    def test_sanction_active_no_update(
            self, application, factory, task, company_sanctions_update_cache,
            ship_update_cache):
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        ship_associate_type = task.check.associate_type
        sis_company = factory.create_sis_company(name=name)
        company_field_name = Ship.get_company_field_name(ship_associate_type)
        ship_data = {
            'imo_id': imo_id,
            company_field_name: sis_company,
        }
        ship = factory.create_ship(**ship_data)
        screening = factory.create_screening(ship=ship, account_id=account_id)
        ship_update_cache.put(str(ship.id), datetime.utcnow())
        cache_key = str(sis_company.id)
        company_sanctions_update_cache.put(cache_key, datetime.utcnow())
        compliance_company = factory.create_compliance_entity(
            entity_type=EntityType.ORGANISATION,
            name=sis_company.name, sis=[sis_company, ])
        factory.create_compliance_sanction(
            sanction_list_name='OFAC - WMD Supporters List',
            compliance_entity_ids={
                compliance_company.id: {
                    'compliance_id': 1,
                    'severity': Severity.CRITICAL,
                    'start_date': '2001-09-11',
                    'end_date': None,
                },
            },
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
            'company_name': name,
            'sanctions': [
                {
                    'sanction_name': 'OFAC - WMD Supporters List',
                    'listed_since': '2001-09-11T00:00:00Z',
                    'listed_to': None,
                    'sanction_severity': 'WARNING',
                },
            ],
        }

    @responses.activate
    def test_sanction_active_update_expired(
            self, application, factory, task, compliance_client,
            ship_update_cache):
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        ship_associate_type = task.check.associate_type
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
            name=sis_company.name, sis=[sis_company, ])
        sanction = factory.create_compliance_sanction(
            sanction_list_name='OFAC - WMD Supporters List',
        )
        factory.create_entity_sanction(
            compliance_entity=compliance_company,
            compliance_sanction=sanction,
            severity=Severity.CRITICAL,
            start_date='2001-09-11',
            end_date=None,
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
                        'organisation_sanctions': [
                            {
                                'id': 140001,
                                'sanction': {
                                    'code': sanction.code,
                                    'name': sanction.sanction_list_name,
                                    'status': 'Current',
                                },
                                'status': 'INACTIVE',
                                'since_date': '2001-09-11',
                                'to_date': '2016-01-16',
                            }
                        ]
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
            'company_name': name,
            'sanctions': [
                {
                    'sanction_name': 'OFAC - WMD Supporters List',
                    'listed_since': '2001-09-11T00:00:00Z',
                    'listed_to': '2016-01-16T00:00:00Z',
                    'sanction_severity': 'OK',
                },
            ],
        }

    @responses.activate
    def test_sanction_nonassoc_update_assoc(
            self, application, factory, task, compliance_client,
            ship_update_cache):
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        ship_associate_type = task.check.associate_type
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
            name=sis_company.name, sis=[sis_company, ])
        compliance_company_2 = factory.create_compliance_entity(
            entity_type=EntityType.ORGANISATION,
            name=sis_company.name)
        sanction = factory.create_compliance_sanction(
            sanction_list_name='OFAC - WMD Supporters List',
        )
        factory.create_entity_sanction(
            compliance_entity=compliance_company_2,
            compliance_sanction=sanction,
            severity=Severity.CRITICAL,
            start_date='2001-09-11',
            end_date=None,
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
                        'organisation_sanctions': [
                            {
                                'id': 140001,
                                'sanction': {
                                    'code': sanction.code,
                                    'name': sanction.sanction_list_name,
                                    'status': 'Current',
                                },
                                'status': 'ACTIVE',
                                'since_date': '2001-09-11',
                                'to_date': None,
                            }
                        ]
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
            'company_name': name,
            'sanctions': [
                {
                    'sanction_name': 'OFAC - WMD Supporters List',
                    'listed_since': '2001-09-11T00:00:00Z',
                    'listed_to': None,
                    'sanction_severity': 'WARNING',
                },
            ],
        }
        assert len(compliance_company_2.sanctions) == 1

    @responses.activate
    def test_sanction_update_added_mapping(
            self, application, factory, task, compliance_client,
            ship_update_cache):
        imo_id = 12345
        account_id = 123456
        name = 'Atlantis'
        ship_associate_type = task.check.associate_type
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
            name=sis_company.name,
        )
        sanction = factory.create_compliance_sanction(
            sanction_list_name='OFAC - WMD Supporters List',
        )
        factory.create_entity_sanction(
            compliance_entity=compliance_company,
            compliance_sanction=sanction,
            severity=Severity.CRITICAL,
            start_date='2001-09-11',
            end_date=None,
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
                        'organisation_sanctions': [
                            {
                                'id': 140001,
                                'sanction': {
                                    'code': sanction.code,
                                    'name': sanction.sanction_list_name,
                                    'status': 'Current',
                                },
                                'status': 'ACTIVE',
                                'since_date': '2001-09-11',
                                'to_date': None,
                            }
                        ]
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
            'company_name': name,
            'sanctions': [
                {
                    'sanction_name': 'OFAC - WMD Supporters List',
                    'listed_since': '2001-09-11T00:00:00Z',
                    'listed_to': None,
                    'sanction_severity': 'WARNING',
                },
            ],
        }
        assert len(compliance_company.sanctions) == 1


class TestShipRegisteredOwnerCheckTask(BaseTestAssociateCompanyTask):

    task_class = ShipRegisteredOwnerCompanyCheckTask


class TestShipOperatorCheckTask(BaseTestAssociateCompanyTask):

    task_class = ShipOperatorCompanyCheckTask


class TestShipBeneficialOwnerCheckTask(BaseTestAssociateCompanyTask):

    task_class = ShipBeneficialOwnerCompanyCheckTask


class TestShipManagerCheckTask(BaseTestAssociateCompanyTask):

    task_class = ShipManagerCompanyCheckTask


class TestShipTechnicalManagerCheckTask(BaseTestAssociateCompanyTask):

    task_class = ShipTechnicalManagerCompanyCheckTask
