from datetime import datetime
import json

from sqlalchemy.orm.exc import NoResultFound

import pytest
import responses

from screening_workers.ships.tasks import ShipCacheUpdateTask


class TestShipCacheUpdateTask:

    @pytest.fixture
    def task(self, application):
        return application.tasks[ShipCacheUpdateTask.name]

    def test_registered(self, application):
        assert ShipCacheUpdateTask.name in application.tasks

    def test_ship_not_found(self, application, factory, task):
        ship_id = 1234567
        task_args = (ship_id, )

        result = task.apply(task_args)

        with pytest.raises(NoResultFound):
            result.get()

        ship = application.ships_repository.get_or_none(id=ship_id)
        assert ship is None

    @responses.activate
    def test_no_update(self, application, factory, task, ship_update_cache):
        imo_id = 12345
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        ship_update_cache.put(str(ship.id), datetime.utcnow())
        task_args = (ship.id, )

        result = task.apply(task_args)

        result.get()

    @responses.activate
    def test_no_sis_ship(self, application, factory, task, sis_client):
        imo_id = 12345
        ship = factory.create_ship(
            imo_id=imo_id, country_id='PL', type='Bulk Carrier')
        response = {
            'objects': [],
        }
        responses.add(
            responses.GET,
            '{0}ships/?imo_id={1}'.format(
                sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (ship.id, )

        result = task.apply(task_args)

        result.get()

    @responses.activate
    def test_update_sis_ship(self, application, factory, task, sis_client):
        imo_id = 12345
        mmsi_old = '999999'
        mmsi_new = '111111'
        ship = factory.create_ship(imo_id=imo_id, mmsi=mmsi_old)
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
                    "group_beneficial_owner": "Meiji Shipping Group",
                    "group_beneficial_owner_company_code": "5231178",
                    "group_beneficial_owner_country_of_control": "Japan",
                    "group_beneficial_owner_country_of_domicile": "Japan",
                    "group_beneficial_owner_country_of_domicile_code": "JPN",
                    "group_beneficial_owner_country_of_registration": "Japan",
                    "image": None,
                    "imo_id": str(imo_id),
                    "length_overall_loa": "183.532",
                    "mmsi": mmsi_new,
                    "operator": "Mitsui OSK Lines Ltd",
                    "operator_company_code": "0153911",
                    "operator_country_of_control": "Japan",
                    "operator_country_of_domicile_code": "JPN",
                    "operator_country_of_domicile_name": "Japan",
                    "operator_country_of_registration": "Japan",
                    "pandi_club": "Unknown",
                    "port_of_registry": "Panama",
                    "registered_owner": "Tohmei Shipping/Bright Ocean",
                    "registered_owner_code": "5188328",
                    "registered_owner_country_of_control": "Japan",
                    "registered_owner_country_of_domicile": "Japan",
                    "registered_owner_country_of_domicile_code": "JPN",
                    "registered_owner_country_of_registration": "Japan",
                    "resource_uri": "/api/v1/ships/8300418",
                    "safety_management_certificate_date_issued": "20090408",
                    "safety_management_certificate_doc_company": "Unknown",
                    "ship_manager": "MMS Co Ltd",
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
                    "technical_manager": "MMS Co Ltd",
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
            '{0}ships/?imo_id={1}'.format(
                sis_client.base_uri, imo_id),
            status=200, body=json.dumps(response),
        )
        task_args = (ship.id, )

        result = task.apply(task_args)

        result_value = result.get()
        assert result_value is None

        ship_updated = application.ships_repository.get_or_none(
            id=ship.id)
        assert ship_updated.mmsi == mmsi_new
