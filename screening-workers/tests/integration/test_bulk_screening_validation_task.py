import json

import pytest
import responses
from sqlalchemy.orm.exc import NoResultFound

from screening_api.screenings.enums import Severity, Status
from screening_api.screenings_bulk.enums import BulkScreeningStatus

from screening_workers.screenings_bulk.tasks import BulkScreeningValidationTask


class TestBulkScreeningValidationTask:

    @pytest.fixture
    def task(self, application):
        return application.tasks[BulkScreeningValidationTask.name]

    def test_registered(self, application):
        assert BulkScreeningValidationTask.name in application.tasks

    def test_bulk_screening_not_found(self, task):
        bulk_screening_id = 121212
        task_args = (bulk_screening_id, )

        result = task.apply(task_args)

        with pytest.raises(NoResultFound):
            result.get()

    @responses.activate
    def test_invalid_imo(
            self, task, factory, application, check_tasks_mock, sis_client):
        imo_id = 9582507
        account_id = 1234567
        bulk_screening = factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.SCHEDULED,
            result=None, imo_id=imo_id)
        task_args = (bulk_screening.id, )

        responses.add(
            responses.GET,
            '{0}ships/?imo_id={1}'.format(
                sis_client.base_uri, bulk_screening.imo_id,
            ),
            status=404,
        )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        bulk_screening = application.bulk_screenings_repository.get_or_none(
            id=bulk_screening.id)
        assert bulk_screening is not None
        assert bulk_screening.status == BulkScreeningStatus.DONE
        assert not bulk_screening.result

        screening = application.screenings_repository.get_or_none(
            account_id=account_id)
        assert screening is None

        assert not check_tasks_mock.doc_company_task.called
        assert not check_tasks_mock.ship_technical_manager_task.called
        assert not check_tasks_mock.ship_manager_task.called
        assert not check_tasks_mock.ship_beneficial_owner_task.called
        assert not check_tasks_mock.ship_operator_task.called
        assert not check_tasks_mock.ship_registered_owner_task.called
        assert not check_tasks_mock.ship_flag_task.called
        assert not check_tasks_mock.ship_flag_task.called
        assert not check_tasks_mock.ship_association_task.called
        assert not check_tasks_mock.ship_sanction_task.called
        assert not check_tasks_mock.port_visits_task.called
        assert not check_tasks_mock.zone_visits_task.called
        assert not check_tasks_mock.ship_inspections_task.called

        assert not check_tasks_mock.ship_reg_owner_company_task.called
        assert not check_tasks_mock.ship_operator_company_task.called
        assert not check_tasks_mock.ship_beneficial_owner_company_task.called
        assert not check_tasks_mock.ship_manager_company_task.called
        assert not check_tasks_mock.ship_technical_manager_company_task.called

    @responses.activate
    def test_existing_ship(
            self, task, factory, application, check_tasks_mock, sis_client):
        imo_id = 9582507
        mmsi = '636015815'
        country_name = 'Liberia'
        account_id = 1234567
        factory.create_ship(
            imo_id=imo_id, mmsi=mmsi, country_name=country_name)
        bulk_screening = factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.SCHEDULED,
            result=None, imo_id=imo_id)
        task_args = (bulk_screening.id, )

        response = {
            "meta": {
                "limit": 20,
                "next": None,
                "offset": 0,
                "previous": None,
                "total_count": 1,
            },
            "objects": [
                {
                    "call_sign": "D5CZ3",
                    "flag": json.dumps({
                        "alt_name": None,
                        "code": "LBR",
                        "iso_3166_1_alpha_2": "LR",
                        "name": country_name,
                        "resource_uri": "",
                        "world_continent": "Africa",
                        "world_region": "Western Africa",
                    }),
                    "flag_name": country_name,
                    "gross_tonnage": 43025.0,
                    "group_beneficial_owner": "Polska Zegluga Morska PP",
                    "id": 103926,
                    "image": "http://net.polestarglobal.sis-photos.s3."
                             "amazonaws.com/1395214_2.jpg",
                    "imo_id": str(imo_id),
                    "length_overall_loa": 228.99000000000001,
                    "mmsi": mmsi,
                    "operator": "Polska Zegluga Morska PP",
                    "port_of_registry": "Monrovia",
                    "registered_owner": "Galatea One Navigation Ltd",
                    "resource_uri": "/api/v1/ship/103926",
                    "ship_manager": "Polska Zegluga Morska PP",
                    "ship_name": "KARPATY",
                    "ship_status": "In Service/Commission",
                    "shiptype_level_5": "Bulk Carrier",
                    "technical_manager": "Polska Zegluga Morska PP",
                    "thumbnail": "http://net.polestarglobal.sis-photos.s3."
                                 "amazonaws.com/1395214_1.jpg",
                    "updated": "2017-09-05T22:36:22.044328",
                    "year_of_build": 2013,
                }
            ]
        }
        responses.add(
            responses.GET,
            '{0}ships/?imo_id={1}'.format(
                sis_client.base_uri, bulk_screening.imo_id,
            ),
            status=200, body=json.dumps(response),
        )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        bulk_screening = application.bulk_screenings_repository.get_or_none(
            id=bulk_screening.id)
        assert bulk_screening is not None
        assert bulk_screening.status == BulkScreeningStatus.DONE
        assert bulk_screening.result

        screening = application.screenings_repository.get_or_none(
            account_id=account_id)
        assert screening is not None
        assert screening.account_id == account_id

        assert screening.status == Status.SCHEDULED
        assert screening.doc_company_status == Status.SCHEDULED
        assert screening.ship_technical_manager_status == Status.SCHEDULED
        assert screening.ship_manager_status == Status.SCHEDULED
        assert screening.ship_beneficial_owner_status == Status.SCHEDULED
        assert screening.ship_operator_status == Status.SCHEDULED
        assert screening.ship_registered_owner_status == Status.SCHEDULED
        assert screening.ship_flag_status == Status.SCHEDULED
        assert screening.ship_association_status == Status.SCHEDULED
        assert screening.ship_sanction_status == Status.SCHEDULED
        assert screening.port_visits_status == Status.SCHEDULED
        assert screening.ship_inspections_status == Status.SCHEDULED
        assert screening.company_sanctions_status == Status.SCHEDULED

        assert screening.ship_registered_owner_company_status ==\
            Status.SCHEDULED
        assert screening.ship_operator_company_status == Status.SCHEDULED
        assert screening.ship_beneficial_owner_company_status ==\
            Status.SCHEDULED
        assert screening.ship_manager_company_status == Status.SCHEDULED
        assert screening.ship_technical_manager_company_status ==\
            Status.SCHEDULED

        assert screening.severity == Severity.UNKNOWN
        assert screening.doc_company_severity == Severity.UNKNOWN
        assert screening.ship_technical_manager_severity == Severity.UNKNOWN
        assert screening.ship_manager_severity == Severity.UNKNOWN
        assert screening.ship_beneficial_owner_severity == Severity.UNKNOWN
        assert screening.ship_operator_severity == Severity.UNKNOWN
        assert screening.ship_registered_owner_severity == Severity.UNKNOWN
        assert screening.ship_flag_severity == Severity.UNKNOWN
        assert screening.ship_association_severity == Severity.UNKNOWN
        assert screening.ship_sanction_severity == Severity.UNKNOWN
        assert screening.port_visits_severity == Severity.UNKNOWN
        assert screening.zone_visits_severity == Severity.UNKNOWN
        assert screening.ship_inspections_severity == Severity.UNKNOWN

        assert screening.ship_registered_owner_company_severity ==\
            Severity.UNKNOWN
        assert screening.ship_operator_company_severity == Severity.UNKNOWN
        assert screening.ship_beneficial_owner_company_severity ==\
            Severity.UNKNOWN
        assert screening.ship_manager_company_severity == Severity.UNKNOWN
        assert screening.ship_technical_manager_company_severity ==\
            Severity.UNKNOWN

        ship = application.ships_repository.get_or_none(
            imo_id=imo_id)
        assert ship is not None
        assert ship.imo_id == imo_id
        assert ship.mmsi == mmsi
        assert ship.country_name == country_name
        assert screening.ship_id == ship.id

        args = (screening.id, )
        check_tasks_mock.doc_company_task.assert_called_once_with(args)
        check_tasks_mock.ship_technical_manager_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_manager_task.assert_called_once_with(args)
        check_tasks_mock.ship_beneficial_owner_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_operator_task.assert_called_once_with(args)
        check_tasks_mock.ship_registered_owner_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_flag_task.assert_called_once_with(args)
        check_tasks_mock.ship_flag_task.assert_called_once_with(args)
        check_tasks_mock.ship_association_task.assert_called_once_with(args)
        check_tasks_mock.ship_sanction_task.assert_called_once_with(args)
        check_tasks_mock.port_visits_task.assert_called_once_with(args)
        check_tasks_mock.zone_visits_task.assert_called_once_with(args)
        check_tasks_mock.ship_inspections_task.assert_called_once_with(args)

        check_tasks_mock.ship_reg_owner_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_operator_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_beneficial_owner_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_manager_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_technical_manager_company_task.\
            assert_called_once_with(args)

    def test_existing_screening(
            self, task, factory, application, check_tasks_mock, sis_client):
        imo_id = 9582507
        mmsi = '636015815'
        country_name = 'Liberia'
        account_id = 1234567
        ship = factory.create_ship(
            imo_id=imo_id, mmsi=mmsi, country_name=country_name)
        screening = factory.create_screening(
            account_id=account_id, ship=ship,

            status=Status.DONE,
            doc_company_status=Status.DONE,
            ship_technical_manager_status=Status.DONE,
            ship_manager_status=Status.DONE,
            ship_beneficial_owner_status=Status.DONE,
            ship_operator_status=Status.DONE,
            ship_registered_owner_status=Status.DONE,
            ship_flag_status=Status.DONE,
            ship_association_status=Status.DONE,
            ship_sanction_status=Status.DONE,
            port_visits_status=Status.DONE,
            ship_inspections_status=Status.DONE,
            ship_registered_owner_company_status=Status.DONE,
            ship_operator_company_status=Status.DONE,
            ship_beneficial_owner_company_status=Status.DONE,
            ship_manager_company_status=Status.DONE,
            ship_technical_manager_company_status=Status.DONE,
            ship_company_associates_status=Status.DONE,

            severity=Severity.OK,
            doc_company_severity=Severity.OK,
            ship_technical_manager_severity=Severity.OK,
            ship_manager_severity=Severity.OK,
            ship_beneficial_owner_severity=Severity.OK,
            ship_operator_severity=Severity.OK,
            ship_registered_owner_severity=Severity.OK,
            ship_flag_severity=Severity.OK,
            ship_association_severity=Severity.OK,
            ship_sanction_severity=Severity.OK,
            port_visits_severity=Severity.OK,
            zone_visits_severity=Severity.OK,
            ship_inspections_severity=Severity.OK,
            ship_registered_owner_company_severity=Severity.OK,
            ship_operator_company_severity=Severity.OK,
            ship_beneficial_owner_company_severity=Severity.OK,
            ship_manager_company_severity=Severity.OK,
            ship_technical_manager_company_severity=Severity.OK,
            ship_company_associates_severity=Severity.OK,
        )
        bulk_screening = factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.SCHEDULED,
            result=None, imo_id=imo_id)
        task_args = (bulk_screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        bulk_screening = application.bulk_screenings_repository.get_or_none(
            id=bulk_screening.id)
        assert bulk_screening is not None
        assert bulk_screening.status == BulkScreeningStatus.DONE
        assert bulk_screening.result

        screening = application.screenings_repository.get_or_none(
            account_id=account_id)
        assert screening is not None
        assert screening.account_id == account_id

        assert screening.status == Status.SCHEDULED
        assert screening.doc_company_status == Status.SCHEDULED
        assert screening.ship_technical_manager_status == Status.SCHEDULED
        assert screening.ship_manager_status == Status.SCHEDULED
        assert screening.ship_beneficial_owner_status == Status.SCHEDULED
        assert screening.ship_operator_status == Status.SCHEDULED
        assert screening.ship_registered_owner_status == Status.SCHEDULED
        assert screening.ship_flag_status == Status.SCHEDULED
        assert screening.ship_association_status == Status.SCHEDULED
        assert screening.ship_sanction_status == Status.SCHEDULED
        assert screening.port_visits_status == Status.SCHEDULED
        assert screening.ship_inspections_status == Status.SCHEDULED
        assert screening.company_sanctions_status == Status.SCHEDULED

        assert screening.ship_registered_owner_company_status ==\
            Status.SCHEDULED
        assert screening.ship_operator_company_status == Status.SCHEDULED
        assert screening.ship_beneficial_owner_company_status ==\
            Status.SCHEDULED
        assert screening.ship_manager_company_status == Status.SCHEDULED
        assert screening.ship_technical_manager_company_status ==\
            Status.SCHEDULED
        assert screening.ship_company_associates_status == Status.SCHEDULED

        assert screening.severity == Severity.OK
        assert screening.doc_company_severity == Severity.OK
        assert screening.ship_technical_manager_severity == Severity.OK
        assert screening.ship_manager_severity == Severity.OK
        assert screening.ship_beneficial_owner_severity == Severity.OK
        assert screening.ship_operator_severity == Severity.OK
        assert screening.ship_registered_owner_severity == Severity.OK
        assert screening.ship_flag_severity == Severity.OK
        assert screening.ship_association_severity == Severity.OK
        assert screening.ship_sanction_severity == Severity.OK
        assert screening.port_visits_severity == Severity.OK
        assert screening.zone_visits_severity == Severity.OK
        assert screening.ship_inspections_severity == Severity.OK

        assert screening.ship_registered_owner_company_severity ==\
            Severity.OK
        assert screening.ship_operator_company_severity == Severity.OK
        assert screening.ship_beneficial_owner_company_severity ==\
            Severity.OK
        assert screening.ship_manager_company_severity == Severity.OK
        assert screening.ship_technical_manager_company_severity ==\
            Severity.OK
        assert screening.ship_company_associates_severity == Severity.OK

        ship = application.ships_repository.get_or_none(
            imo_id=imo_id)
        assert ship is not None
        assert ship.imo_id == imo_id
        assert ship.mmsi == mmsi
        assert ship.country_name == country_name
        assert screening.ship_id == ship.id

        args = (screening.id, )
        check_tasks_mock.doc_company_task.assert_called_once_with(args)
        check_tasks_mock.ship_technical_manager_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_manager_task.assert_called_once_with(args)
        check_tasks_mock.ship_beneficial_owner_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_operator_task.assert_called_once_with(args)
        check_tasks_mock.ship_registered_owner_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_flag_task.assert_called_once_with(args)
        check_tasks_mock.ship_flag_task.assert_called_once_with(args)
        check_tasks_mock.ship_association_task.assert_called_once_with(args)
        check_tasks_mock.ship_sanction_task.assert_called_once_with(args)
        check_tasks_mock.port_visits_task.assert_called_once_with(args)
        check_tasks_mock.zone_visits_task.assert_called_once_with(args)
        check_tasks_mock.ship_inspections_task.assert_called_once_with(args)

        check_tasks_mock.ship_reg_owner_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_operator_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_beneficial_owner_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_manager_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_technical_manager_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_company_associates_task.\
            assert_called_once_with(args)

        history = application.screenings_history_repository.get_or_none(
            screening_id=screening.id)
        assert history is not None
        assert history.screening_id == screening.id
        assert history.severity == Severity.OK
        assert history.doc_company_severity == Severity.OK
        assert history.ship_technical_manager_severity == Severity.OK
        assert history.ship_manager_severity == Severity.OK
        assert history.ship_beneficial_owner_severity == Severity.OK
        assert history.ship_operator_severity == Severity.OK
        assert history.ship_registered_owner_severity == Severity.OK
        assert history.ship_flag_severity == Severity.OK
        assert history.ship_association_severity == Severity.OK
        assert history.ship_sanction_severity == Severity.OK
        assert history.port_visits_severity == Severity.OK
        assert history.zone_visits_severity == Severity.OK
        assert history.ship_inspections_severity == Severity.OK
        assert history.ship_registered_owner_company_severity == Severity.OK
        assert history.ship_operator_company_severity == Severity.OK
        assert history.ship_beneficial_owner_company_severity == Severity.OK
        assert history.ship_manager_company_severity == Severity.OK
        assert history.ship_technical_manager_company_severity == Severity.OK
        assert history.ship_company_associates_severity == Severity.OK

    def test_existing_screening_not_completed(
            self, task, factory, application, check_tasks_mock, sis_client):
        imo_id = 9582507
        mmsi = '636015815'
        country_name = 'Liberia'
        account_id = 1234567
        ship = factory.create_ship(
            imo_id=imo_id, mmsi=mmsi, country_name=country_name)
        screening = factory.create_screening(
            account_id=account_id, ship=ship,

            status=Status.PENDING,
            doc_company_status=Status.PENDING,
            ship_technical_manager_status=Status.PENDING,
            ship_manager_status=Status.PENDING,
            ship_beneficial_owner_status=Status.PENDING,
            ship_operator_status=Status.PENDING,
            ship_registered_owner_status=Status.PENDING,
            ship_flag_status=Status.PENDING,
            ship_association_status=Status.PENDING,
            ship_sanction_status=Status.PENDING,
            port_visits_status=Status.PENDING,
            ship_inspections_status=Status.PENDING,
            ship_registered_owner_company_status=Status.PENDING,
            ship_operator_company_status=Status.PENDING,
            ship_beneficial_owner_company_status=Status.PENDING,
            ship_manager_company_status=Status.PENDING,
            ship_technical_manager_company_status=Status.PENDING,

            severity=Severity.OK,
            doc_company_severity=Severity.OK,
            ship_technical_manager_severity=Severity.OK,
            ship_manager_severity=Severity.OK,
            ship_beneficial_owner_severity=Severity.OK,
            ship_operator_severity=Severity.OK,
            ship_registered_owner_severity=Severity.OK,
            ship_flag_severity=Severity.OK,
            ship_association_severity=Severity.OK,
            ship_sanction_severity=Severity.OK,
            port_visits_severity=Severity.OK,
            zone_visits_severity=Severity.OK,
            ship_inspections_severity=Severity.OK,
            ship_registered_owner_company_severity=Severity.OK,
            ship_operator_company_severity=Severity.OK,
            ship_beneficial_owner_company_severity=Severity.OK,
            ship_manager_company_severity=Severity.OK,
            ship_technical_manager_company_severity=Severity.OK,
        )
        bulk_screening = factory.create_bulk_screening(
            account_id=account_id, status=BulkScreeningStatus.SCHEDULED,
            result=None, imo_id=imo_id)
        task_args = (bulk_screening.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        bulk_screening = application.bulk_screenings_repository.get_or_none(
            id=bulk_screening.id)
        assert bulk_screening is not None
        assert bulk_screening.status == BulkScreeningStatus.DONE
        assert bulk_screening.result

        screening = application.screenings_repository.get_or_none(
            account_id=account_id)
        assert screening is not None
        assert screening.account_id == account_id

        assert screening.status == Status.PENDING
        assert screening.doc_company_status == Status.PENDING
        assert screening.ship_technical_manager_status == Status.PENDING
        assert screening.ship_manager_status == Status.PENDING
        assert screening.ship_beneficial_owner_status == Status.PENDING
        assert screening.ship_operator_status == Status.PENDING
        assert screening.ship_registered_owner_status == Status.PENDING
        assert screening.ship_flag_status == Status.PENDING
        assert screening.ship_association_status == Status.PENDING
        assert screening.ship_sanction_status == Status.PENDING
        assert screening.port_visits_status == Status.PENDING
        assert screening.ship_inspections_status == Status.PENDING
        assert screening.company_sanctions_status == Status.PENDING

        assert screening.ship_registered_owner_company_status ==\
            Status.PENDING
        assert screening.ship_operator_company_status == Status.PENDING
        assert screening.ship_beneficial_owner_company_status ==\
            Status.PENDING
        assert screening.ship_manager_company_status == Status.PENDING
        assert screening.ship_technical_manager_company_status ==\
            Status.PENDING

        assert screening.severity == Severity.OK
        assert screening.doc_company_severity == Severity.OK
        assert screening.ship_technical_manager_severity == Severity.OK
        assert screening.ship_manager_severity == Severity.OK
        assert screening.ship_beneficial_owner_severity == Severity.OK
        assert screening.ship_operator_severity == Severity.OK
        assert screening.ship_registered_owner_severity == Severity.OK
        assert screening.ship_flag_severity == Severity.OK
        assert screening.ship_association_severity == Severity.OK
        assert screening.ship_sanction_severity == Severity.OK
        assert screening.port_visits_severity == Severity.OK
        assert screening.zone_visits_severity == Severity.OK
        assert screening.ship_inspections_severity == Severity.OK

        assert screening.ship_registered_owner_company_severity ==\
            Severity.OK
        assert screening.ship_operator_company_severity == Severity.OK
        assert screening.ship_beneficial_owner_company_severity ==\
            Severity.OK
        assert screening.ship_manager_company_severity == Severity.OK
        assert screening.ship_technical_manager_company_severity ==\
            Severity.OK

        ship = application.ships_repository.get_or_none(
            imo_id=imo_id)
        assert ship is not None
        assert ship.imo_id == imo_id
        assert ship.mmsi == mmsi
        assert ship.country_name == country_name
        assert screening.ship_id == ship.id

        assert not check_tasks_mock.doc_company_task.called
        assert not check_tasks_mock.ship_technical_manager_task.called
        assert not check_tasks_mock.ship_manager_task.called
        assert not check_tasks_mock.ship_beneficial_owner_task.called
        assert not check_tasks_mock.ship_operator_task.called
        assert not check_tasks_mock.ship_registered_owner_task.called
        assert not check_tasks_mock.ship_flag_task.called
        assert not check_tasks_mock.ship_flag_task.called
        assert not check_tasks_mock.ship_association_task.called
        assert not check_tasks_mock.ship_sanction_task.called
        assert not check_tasks_mock.port_visits_task.called
        assert not check_tasks_mock.zone_visits_task.called
        assert not check_tasks_mock.ship_inspections_task.called

        assert not check_tasks_mock.ship_reg_owner_company_task.called
        assert not check_tasks_mock.ship_operator_company_task.called
        assert not check_tasks_mock.ship_beneficial_owner_company_task.called
        assert not check_tasks_mock.ship_manager_company_task.called
        assert not check_tasks_mock.ship_technical_manager_company_task.called

    @responses.activate
    def test_new_ship(
            self, task, factory, application, check_tasks_mock, sis_client):
        imo_id = 9582507
        mmsi = '636015815'
        country_id = 'LR'
        country_name = 'Liberia'
        account_id = 1234567
        bulk_screening = factory.create_bulk_screening(
            status=BulkScreeningStatus.SCHEDULED, result=None, imo_id=imo_id,
            account_id=account_id,
        )
        task_args = (bulk_screening.id, )

        response = {
            "meta": {
                "limit": 20,
                "next": None,
                "offset": 0,
                "previous": None,
                "total_count": 1,
            },
            "objects": [
                {
                    "call_sign": "D5CZ3",
                    "flag": json.dumps({
                        "alt_name": None,
                        "code": "LBR",
                        "iso_3166_1_alpha_2": country_id,
                        "name": country_name,
                        "resource_uri": "",
                        "world_continent": "Africa",
                        "world_region": "Western Africa",
                    }),
                    "flag_name": country_name,
                    "gross_tonnage": 43025,
                    "group_beneficial_owner": "Polska Zegluga Morska PP",
                    "id": 103926,
                    "image": "http://net.polestarglobal.sis-photos.s3."
                             "amazonaws.com/1395214_2.jpg",
                    "imo_id": str(imo_id),
                    "length_overall_loa": 228.99,
                    "mmsi": mmsi,
                    "operator": "Polska Zegluga Morska PP",
                    "port_of_registry": "Monrovia",
                    "registered_owner": "Galatea One Navigation Ltd",
                    "resource_uri": "/api/v1/ship/103926",
                    "ship_manager": "Polska Zegluga Morska PP",
                    "ship_name": "KARPATY",
                    "ship_status": "In Service/Commission",
                    "shiptype_level_5": "Bulk Carrier",
                    "technical_manager": "Polska Zegluga Morska PP",
                    "thumbnail": "http://net.polestarglobal.sis-photos.s3."
                                 "amazonaws.com/1395214_1.jpg",
                    "updated": "2017-09-05T22:36:22.044328",
                    "year_of_build": 2013,
                }
            ]
        }
        responses.add(
            responses.GET,
            '{0}ships/?imo_id={1}'.format(
                sis_client.base_uri, bulk_screening.imo_id,
            ),
            status=200, body=json.dumps(response),
        )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        bulk_screening = application.bulk_screenings_repository.get_or_none(
            id=bulk_screening.id)
        assert bulk_screening is not None
        assert bulk_screening.status == BulkScreeningStatus.DONE
        assert bulk_screening.result

        screening = application.screenings_repository.get_or_none(
            account_id=account_id)
        assert screening is not None
        assert screening.account_id == account_id

        assert screening.status == Status.SCHEDULED
        assert screening.doc_company_status == Status.SCHEDULED
        assert screening.ship_technical_manager_status == Status.SCHEDULED
        assert screening.ship_manager_status == Status.SCHEDULED
        assert screening.ship_beneficial_owner_status == Status.SCHEDULED
        assert screening.ship_operator_status == Status.SCHEDULED
        assert screening.ship_registered_owner_status == Status.SCHEDULED
        assert screening.ship_flag_status == Status.SCHEDULED
        assert screening.ship_association_status == Status.SCHEDULED
        assert screening.ship_sanction_status == Status.SCHEDULED
        assert screening.port_visits_status == Status.SCHEDULED
        assert screening.ship_inspections_status == Status.SCHEDULED
        assert screening.ship_registered_owner_company_status ==\
            Status.SCHEDULED
        assert screening.ship_operator_company_status == Status.SCHEDULED
        assert screening.ship_beneficial_owner_company_status ==\
            Status.SCHEDULED
        assert screening.ship_manager_company_status == Status.SCHEDULED
        assert screening.ship_technical_manager_company_status ==\
            Status.SCHEDULED

        assert screening.severity == Severity.UNKNOWN
        assert screening.doc_company_severity == Severity.UNKNOWN
        assert screening.ship_technical_manager_severity == Severity.UNKNOWN
        assert screening.ship_manager_severity == Severity.UNKNOWN
        assert screening.ship_beneficial_owner_severity == Severity.UNKNOWN
        assert screening.ship_operator_severity == Severity.UNKNOWN
        assert screening.ship_registered_owner_severity == Severity.UNKNOWN
        assert screening.ship_flag_severity == Severity.UNKNOWN
        assert screening.ship_association_severity == Severity.UNKNOWN
        assert screening.ship_sanction_severity == Severity.UNKNOWN
        assert screening.port_visits_severity == Severity.UNKNOWN
        assert screening.zone_visits_severity == Severity.UNKNOWN
        assert screening.ship_inspections_severity == Severity.UNKNOWN
        assert screening.ship_registered_owner_company_severity ==\
            Severity.UNKNOWN
        assert screening.ship_operator_company_severity == Severity.UNKNOWN
        assert screening.ship_beneficial_owner_company_severity ==\
            Severity.UNKNOWN
        assert screening.ship_manager_company_severity == Severity.UNKNOWN
        assert screening.ship_technical_manager_company_severity ==\
            Severity.UNKNOWN

        ship = application.ships_repository.get_or_none(
            imo_id=imo_id)
        assert ship is not None
        assert ship.imo_id == imo_id
        assert ship.mmsi == mmsi
        assert ship.country_id == country_id
        assert ship.country_name == country_name
        assert screening.ship_id == ship.id

        args = (screening.id, )
        check_tasks_mock.doc_company_task.assert_called_once_with(args)
        check_tasks_mock.ship_technical_manager_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_manager_task.assert_called_once_with(args)
        check_tasks_mock.ship_beneficial_owner_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_operator_task.assert_called_once_with(args)
        check_tasks_mock.ship_registered_owner_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_flag_task.assert_called_once_with(args)
        check_tasks_mock.ship_flag_task.assert_called_once_with(args)
        check_tasks_mock.ship_association_task.assert_called_once_with(args)
        check_tasks_mock.ship_sanction_task.assert_called_once_with(args)
        check_tasks_mock.port_visits_task.assert_called_once_with(args)
        check_tasks_mock.zone_visits_task.assert_called_once_with(args)
        check_tasks_mock.ship_inspections_task.assert_called_once_with(args)

        check_tasks_mock.ship_reg_owner_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_operator_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_beneficial_owner_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_manager_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_technical_manager_company_task.\
            assert_called_once_with(args)

    @responses.activate
    def test_new_ship_non_ascii_name(
            self, task, factory, application, check_tasks_mock, sis_client):
        imo_id = 9582507
        mmsi = '636015815'
        country_name = 'Liberia'
        account_id = 1234567
        ship_name = (
            "AAAQATest22_2017/03/13_Honeywell_"
            "Unit_ôûÂÊÎÔÛäëïöüåÅß¡¿øØ"
        )
        bulk_screening = factory.create_bulk_screening(
            status=BulkScreeningStatus.SCHEDULED, result=None, imo_id=imo_id,
            account_id=account_id,
        )
        task_args = (bulk_screening.id, )

        response = {
            "meta": {
                "limit": 20,
                "next": None,
                "offset": 0,
                "previous": None,
                "total_count": 1,
            },
            "objects": [
                {
                    "call_sign": "D5CZ3",
                    "flag": json.dumps({
                        "alt_name": None,
                        "code": "LBR",
                        "iso_3166_1_alpha_2": "LR",
                        "name": country_name,
                        "resource_uri": "",
                        "world_continent": "Africa",
                        "world_region": "Western Africa",
                    }),
                    "flag_name": country_name,
                    "gross_tonnage": '43025',
                    "group_beneficial_owner": "Polska Zegluga Morska PP",
                    "id": 103926,
                    "image": "http://net.polestarglobal.sis-photos.s3."
                             "amazonaws.com/1395214_2.jpg",
                    "imo_id": str(imo_id),
                    "length_overall_loa": 228.99,
                    "mmsi": "636015815",
                    "operator": "Polska Zegluga Morska PP",
                    "port_of_registry": "Monrovia",
                    "registered_owner": "Galatea One Navigation Ltd",
                    "resource_uri": "/api/v1/ship/103926",
                    "ship_manager": "Polska Zegluga Morska PP",
                    "ship_name": ship_name,
                    "ship_status": "In Service/Commission",
                    "shiptype_level_5": "Bulk Carrier",
                    "technical_manager": "Polska Zegluga Morska PP",
                    "thumbnail": "http://net.polestarglobal.sis-photos.s3."
                                 "amazonaws.com/1395214_1.jpg",
                    "updated": "2017-09-05T22:36:22.044328",
                    "year_of_build": 2013,
                }
            ]
        }
        responses.add(
            responses.GET,
            '{0}ships/?imo_id={1}'.format(
                sis_client.base_uri, bulk_screening.imo_id,
            ),
            status=200, body=json.dumps(response),
        )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        bulk_screening = application.bulk_screenings_repository.get_or_none(
            id=bulk_screening.id)
        assert bulk_screening is not None
        assert bulk_screening.status == BulkScreeningStatus.DONE
        assert bulk_screening.result

        screening = application.screenings_repository.get_or_none(
            account_id=account_id)
        assert screening is not None
        assert screening.account_id == account_id

        assert screening.status == Status.SCHEDULED
        assert screening.doc_company_status == Status.SCHEDULED
        assert screening.ship_technical_manager_status == Status.SCHEDULED
        assert screening.ship_manager_status == Status.SCHEDULED
        assert screening.ship_beneficial_owner_status == Status.SCHEDULED
        assert screening.ship_operator_status == Status.SCHEDULED
        assert screening.ship_registered_owner_status == Status.SCHEDULED
        assert screening.ship_flag_status == Status.SCHEDULED
        assert screening.ship_association_status == Status.SCHEDULED
        assert screening.ship_sanction_status == Status.SCHEDULED
        assert screening.port_visits_status == Status.SCHEDULED
        assert screening.ship_inspections_status == Status.SCHEDULED
        assert screening.ship_registered_owner_company_status ==\
            Status.SCHEDULED
        assert screening.ship_operator_company_status == Status.SCHEDULED
        assert screening.ship_beneficial_owner_company_status ==\
            Status.SCHEDULED
        assert screening.ship_manager_company_status == Status.SCHEDULED
        assert screening.ship_technical_manager_company_status ==\
            Status.SCHEDULED

        assert screening.severity == Severity.UNKNOWN
        assert screening.doc_company_severity == Severity.UNKNOWN
        assert screening.ship_technical_manager_severity == Severity.UNKNOWN
        assert screening.ship_manager_severity == Severity.UNKNOWN
        assert screening.ship_beneficial_owner_severity == Severity.UNKNOWN
        assert screening.ship_operator_severity == Severity.UNKNOWN
        assert screening.ship_registered_owner_severity == Severity.UNKNOWN
        assert screening.ship_flag_severity == Severity.UNKNOWN
        assert screening.ship_association_severity == Severity.UNKNOWN
        assert screening.ship_sanction_severity == Severity.UNKNOWN
        assert screening.port_visits_severity == Severity.UNKNOWN
        assert screening.zone_visits_severity == Severity.UNKNOWN
        assert screening.ship_inspections_severity == Severity.UNKNOWN
        assert screening.ship_registered_owner_company_severity ==\
            Severity.UNKNOWN
        assert screening.ship_operator_company_severity == Severity.UNKNOWN
        assert screening.ship_beneficial_owner_company_severity ==\
            Severity.UNKNOWN
        assert screening.ship_manager_company_severity == Severity.UNKNOWN
        assert screening.ship_technical_manager_company_severity ==\
            Severity.UNKNOWN

        ship = application.ships_repository.get_or_none(
            imo_id=imo_id)
        assert ship is not None
        assert ship.imo_id == imo_id
        assert ship.mmsi == mmsi
        assert ship.country_name == country_name
        assert ship.name == ship_name
        assert screening.ship_id == ship.id

        args = (screening.id, )
        check_tasks_mock.doc_company_task.assert_called_once_with(args)
        check_tasks_mock.ship_technical_manager_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_manager_task.assert_called_once_with(args)
        check_tasks_mock.ship_beneficial_owner_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_operator_task.assert_called_once_with(args)
        check_tasks_mock.ship_registered_owner_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_flag_task.assert_called_once_with(args)
        check_tasks_mock.ship_flag_task.assert_called_once_with(args)
        check_tasks_mock.ship_association_task.assert_called_once_with(args)
        check_tasks_mock.ship_sanction_task.assert_called_once_with(args)
        check_tasks_mock.port_visits_task.assert_called_once_with(args)
        check_tasks_mock.zone_visits_task.assert_called_once_with(args)
        check_tasks_mock.ship_inspections_task.assert_called_once_with(args)

        check_tasks_mock.ship_reg_owner_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_operator_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_beneficial_owner_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_manager_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_technical_manager_company_task.\
            assert_called_once_with(args)

    @responses.activate
    def test_new_ship_no_flag(
            self, task, factory, application, check_tasks_mock, sis_client):
        imo_id = 9582507
        mmsi = '636015815'
        account_id = 1234567
        bulk_screening = factory.create_bulk_screening(
            status=BulkScreeningStatus.SCHEDULED, result=None, imo_id=imo_id,
            account_id=account_id,
        )
        task_args = (bulk_screening.id, )

        response = {
            "meta": {
                "limit": 20,
                "next": None,
                "offset": 0,
                "previous": None,
                "total_count": 1,
            },
            "objects": [
                {
                    "call_sign": "D5CZ3",
                    "flag": None,
                    "flag_name": "Liberia",
                    "gross_tonnage": 43025,
                    "group_beneficial_owner": "Polska Zegluga Morska PP",
                    "id": 103926,
                    "image": "http://net.polestarglobal.sis-photos.s3."
                             "amazonaws.com/1395214_2.jpg",
                    "imo_id": str(imo_id),
                    "length_overall_loa": 228.99,
                    "mmsi": mmsi,
                    "operator": "Polska Zegluga Morska PP",
                    "port_of_registry": "Monrovia",
                    "registered_owner": "Galatea One Navigation Ltd",
                    "resource_uri": "/api/v1/ship/103926",
                    "ship_manager": "Polska Zegluga Morska PP",
                    "ship_name": "KARPATY",
                    "ship_status": "In Service/Commission",
                    "shiptype_level_5": "Bulk Carrier",
                    "technical_manager": "Polska Zegluga Morska PP",
                    "thumbnail": "http://net.polestarglobal.sis-photos.s3."
                                 "amazonaws.com/1395214_1.jpg",
                    "updated": "2017-09-05T22:36:22.044328",
                    "year_of_build": 2013,
                }
            ]
        }
        responses.add(
            responses.GET,
            '{0}ships/?imo_id={1}'.format(
                sis_client.base_uri, bulk_screening.imo_id,
            ),
            status=200, body=json.dumps(response),
        )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        bulk_screening = application.bulk_screenings_repository.get_or_none(
            id=bulk_screening.id)
        assert bulk_screening is not None
        assert bulk_screening.status == BulkScreeningStatus.DONE
        assert bulk_screening.result

        screening = application.screenings_repository.get_or_none(
            account_id=account_id)
        assert screening is not None

        assert screening.status == Status.SCHEDULED
        assert screening.doc_company_status == Status.SCHEDULED
        assert screening.ship_technical_manager_status == Status.SCHEDULED
        assert screening.ship_manager_status == Status.SCHEDULED
        assert screening.ship_beneficial_owner_status == Status.SCHEDULED
        assert screening.ship_operator_status == Status.SCHEDULED
        assert screening.ship_registered_owner_status == Status.SCHEDULED
        assert screening.ship_flag_status == Status.SCHEDULED
        assert screening.ship_association_status == Status.SCHEDULED
        assert screening.ship_sanction_status == Status.SCHEDULED
        assert screening.port_visits_status == Status.SCHEDULED
        assert screening.ship_inspections_status == Status.SCHEDULED
        assert screening.ship_registered_owner_company_status ==\
            Status.SCHEDULED
        assert screening.ship_operator_company_status == Status.SCHEDULED
        assert screening.ship_beneficial_owner_company_status ==\
            Status.SCHEDULED
        assert screening.ship_manager_company_status == Status.SCHEDULED
        assert screening.ship_technical_manager_company_status ==\
            Status.SCHEDULED

        assert screening.severity == Severity.UNKNOWN
        assert screening.doc_company_severity == Severity.UNKNOWN
        assert screening.ship_technical_manager_severity == Severity.UNKNOWN
        assert screening.ship_manager_severity == Severity.UNKNOWN
        assert screening.ship_beneficial_owner_severity == Severity.UNKNOWN
        assert screening.ship_operator_severity == Severity.UNKNOWN
        assert screening.ship_registered_owner_severity == Severity.UNKNOWN
        assert screening.ship_flag_severity == Severity.UNKNOWN
        assert screening.ship_association_severity == Severity.UNKNOWN
        assert screening.ship_sanction_severity == Severity.UNKNOWN
        assert screening.port_visits_severity == Severity.UNKNOWN
        assert screening.zone_visits_severity == Severity.UNKNOWN
        assert screening.ship_inspections_severity == Severity.UNKNOWN
        assert screening.ship_registered_owner_company_severity ==\
            Severity.UNKNOWN
        assert screening.ship_operator_company_severity == Severity.UNKNOWN
        assert screening.ship_beneficial_owner_company_severity ==\
            Severity.UNKNOWN
        assert screening.ship_manager_company_severity == Severity.UNKNOWN
        assert screening.ship_technical_manager_company_severity ==\
            Severity.UNKNOWN

        ship = application.ships_repository.get_or_none(
            imo_id=imo_id)
        assert ship is not None
        assert ship.imo_id == imo_id
        assert ship.mmsi == mmsi
        assert screening.ship_id == ship.id

        args = (screening.id, )
        check_tasks_mock.doc_company_task.assert_called_once_with(args)
        check_tasks_mock.ship_technical_manager_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_manager_task.assert_called_once_with(args)
        check_tasks_mock.ship_beneficial_owner_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_operator_task.assert_called_once_with(args)
        check_tasks_mock.ship_registered_owner_task.assert_called_once_with(
            args)
        check_tasks_mock.ship_flag_task.assert_called_once_with(args)
        check_tasks_mock.ship_flag_task.assert_called_once_with(args)
        check_tasks_mock.ship_association_task.assert_called_once_with(args)
        check_tasks_mock.ship_sanction_task.assert_called_once_with(args)
        check_tasks_mock.port_visits_task.assert_called_once_with(args)
        check_tasks_mock.zone_visits_task.assert_called_once_with(args)
        check_tasks_mock.ship_inspections_task.assert_called_once_with(args)

        check_tasks_mock.ship_reg_owner_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_operator_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_beneficial_owner_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_manager_company_task.\
            assert_called_once_with(args)
        check_tasks_mock.ship_technical_manager_company_task.\
            assert_called_once_with(args)
