import json
from datetime import date, timedelta

from django.test import TestCase

from tastypie.test import ResourceTestCaseMixin

from ships.tests.factories import (
    ShipDefectFactory,
    ShipInspectionFactory,
    UserFactory
)


class ShipInspectionResource(ResourceTestCaseMixin, TestCase):
    def setUp(self):
        self.maxDiff = None

        self.user = UserFactory.create()
        self.client.login(username=self.user.username, password='letmein')

        self.ship_inspection = ShipInspectionFactory.create()
        self.ship_defect = ShipDefectFactory.create(
            inspection=self.ship_inspection
        )

    def test_get_inspections_list(self):
        """ List all ``ShipInspection`` objects. """
        # Create another `ShipInspection`, for another different ship.
        ship_inspection_2 = ShipInspectionFactory.create()

        response = self.client.get('/api/v1/inspections', format='json')

        self.assertEqual(response.status_code, 200)

        expected = {
            'meta': {
                'limit': 20,
                'next': None,
                'offset': 0,
                'previous': None,
                'total_count': 2
            },
            'objects': [
                {
                    'authorisation': self.ship_inspection.authorisation,
                    'call_sign': self.ship_inspection.call_sign,
                    'cargo': self.ship_inspection.cargo,
                    'charterer': self.ship_inspection.charterer,
                    'country_name': self.ship_inspection.country_name,
                    'date_release': self.ship_inspection.date_release,
                    'defects': [
                        {
                            'action_1': self.ship_defect.action_1,
                            'action_2': self.ship_defect.action_2,
                            'action_3': self.ship_defect.action_3,
                            'action_code_1': self.ship_defect.action_code_1,
                            'action_code_2': self.ship_defect.action_code_2,
                            'action_code_3': self.ship_defect.action_code_3,
                            'class_is_responsible':
                                self.ship_defect.class_is_responsible,
                            'defect_code': self.ship_defect.defect_code,
                            'defect_id': self.ship_defect.defect_id,
                            'defect_text': self.ship_defect.defect_text,
                            'detention_reason_deficiency':
                                self.ship_defect.detention_reason_deficiency,
                            'inspection':
                                f'/api/v1/inspections/'
                                f'{self.ship_defect.inspection.inspection_id}',
                            'main_defect_code':
                                self.ship_defect.main_defect_code,
                            'main_defect_text':
                                self.ship_defect.main_defect_text,
                            'other_action': self.ship_defect.other_action,
                            'other_recognised_org_resp':
                                self.ship_defect.other_recognised_org_resp,
                            'recognised_org_resp':
                                self.ship_defect.recognised_org_resp,
                            'recognised_org_resp_code':
                                self.ship_defect.recognised_org_resp_code,
                            'recognised_org_resp_yn':
                                self.ship_defect.recognised_org_resp_yn,
                            'resource_uri':
                                f'/api/v1/defects/{self.ship_defect.pk}'
                        }
                    ],
                    'detained': self.ship_inspection.detained,
                    'dwt': self.ship_inspection.dwt,
                    'expanded_inspection':
                        self.ship_inspection.expanded_inspection,
                    'flag_name': self.ship_inspection.flag_name,
                    'gt': self.ship_inspection.gt,
                    'imo_id': self.ship_inspection.imo_id,
                    'inspection_date': self.ship_inspection.inspection_date,
                    'inspection_id': self.ship_inspection.inspection_id,
                    'manager': self.ship_inspection.manager,
                    'no_days_detained': self.ship_inspection.no_days_detained,
                    'no_defects': self.ship_inspection.no_defects,
                    'number_part_days_detained':
                        str(self.ship_inspection.number_part_days_detained),
                    'other_inspection_type':
                        self.ship_inspection.other_inspection_type,
                    'owner': self.ship_inspection.owner,
                    'port_name': self.ship_inspection.port_name,
                    'resource_uri':
                        f'/api/v1/inspections/'
                        f'{self.ship_inspection.inspection_id}',
                    'ship_name': self.ship_inspection.ship_name,
                    'shipclass': self.ship_inspection.shipclass,
                    'shiptype': self.ship_inspection.shiptype,
                    'source': self.ship_inspection.source,
                    'yob': self.ship_inspection.yob
                },
                {
                    'authorisation': ship_inspection_2.authorisation,
                    'call_sign': ship_inspection_2.call_sign,
                    'cargo': ship_inspection_2.cargo,
                    'charterer': ship_inspection_2.charterer,
                    'country_name': ship_inspection_2.country_name,
                    'date_release': ship_inspection_2.date_release,
                    'defects': [],
                    'detained': ship_inspection_2.detained,
                    'dwt': ship_inspection_2.dwt,
                    'expanded_inspection':
                        ship_inspection_2.expanded_inspection,
                    'flag_name': ship_inspection_2.flag_name,
                    'gt': ship_inspection_2.gt,
                    'imo_id': ship_inspection_2.imo_id,
                    'inspection_date': ship_inspection_2.inspection_date,
                    'inspection_id': ship_inspection_2.inspection_id,
                    'manager': ship_inspection_2.manager,
                    'no_days_detained': ship_inspection_2.no_days_detained,
                    'no_defects': ship_inspection_2.no_defects,
                    'number_part_days_detained':
                        str(ship_inspection_2.number_part_days_detained),
                    'other_inspection_type':
                        ship_inspection_2.other_inspection_type,
                    'owner': ship_inspection_2.owner,
                    'port_name': ship_inspection_2.port_name,
                    'resource_uri':
                        f'/api/v1/inspections/'
                        f'{ship_inspection_2.inspection_id}',
                    'ship_name': ship_inspection_2.ship_name,
                    'shipclass': ship_inspection_2.shipclass,
                    'shiptype': ship_inspection_2.shiptype,
                    'source': ship_inspection_2.source,
                    'yob': ship_inspection_2.yob
                }
            ]
        }

        data = json.loads(response.content)
        self.assertEqual(data, expected)

    def test_get_inspections_list_filter_imo_number(self):
        """ List all ``ShipInspection`` objects FILTERED for a certain IMO. """
        # Create another `ShipInspection` for a different ship, and another one
        # for the same ship in `self.ship_inspection`.
        ShipInspectionFactory.create()
        ship_inspection_2 = ShipInspectionFactory.create(
            imo_id=self.ship_inspection.imo_id,
            inspection_date=str(date.today() + timedelta(days=1))
        )

        response = self.client.get(
            f'/api/v1/ships/{self.ship_inspection.imo_id}/inspections',
            format='json'
        )

        self.assertEqual(response.status_code, 200)

        # Results show ONLY 2 inspections: the ones for
        # `self.ship_inspection.imo_id`.

        expected = {
            'meta': {
                'limit': 20,
                'next': None,
                'offset': 0,
                'previous': None,
                'total_count': 2
            },
            'objects': [
                {
                    'authorisation': ship_inspection_2.authorisation,
                    'call_sign': ship_inspection_2.call_sign,
                    'cargo': ship_inspection_2.cargo,
                    'charterer': ship_inspection_2.charterer,
                    'country_name': ship_inspection_2.country_name,
                    'date_release': ship_inspection_2.date_release,
                    'defects': [],
                    'detained': ship_inspection_2.detained,
                    'dwt': ship_inspection_2.dwt,
                    'expanded_inspection':
                        ship_inspection_2.expanded_inspection,
                    'flag_name': ship_inspection_2.flag_name,
                    'gt': ship_inspection_2.gt,
                    'imo_id': ship_inspection_2.imo_id,
                    'inspection_date': ship_inspection_2.inspection_date,
                    'inspection_id': ship_inspection_2.inspection_id,
                    'manager': ship_inspection_2.manager,
                    'no_days_detained': ship_inspection_2.no_days_detained,
                    'no_defects': ship_inspection_2.no_defects,
                    'number_part_days_detained':
                        str(ship_inspection_2.number_part_days_detained),
                    'other_inspection_type':
                        ship_inspection_2.other_inspection_type,
                    'owner': ship_inspection_2.owner,
                    'port_name': ship_inspection_2.port_name,
                    'resource_uri':
                        f'/api/v1/inspections/'
                        f'{ship_inspection_2.inspection_id}',
                    'ship_name': ship_inspection_2.ship_name,
                    'shipclass': ship_inspection_2.shipclass,
                    'shiptype': ship_inspection_2.shiptype,
                    'source': ship_inspection_2.source,
                    'yob': ship_inspection_2.yob
                },
                {
                    'authorisation': self.ship_inspection.authorisation,
                    'call_sign': self.ship_inspection.call_sign,
                    'cargo': self.ship_inspection.cargo,
                    'charterer': self.ship_inspection.charterer,
                    'country_name': self.ship_inspection.country_name,
                    'date_release': self.ship_inspection.date_release,
                    'defects': [
                        {
                            'action_1': self.ship_defect.action_1,
                            'action_2': self.ship_defect.action_2,
                            'action_3': self.ship_defect.action_3,
                            'action_code_1': self.ship_defect.action_code_1,
                            'action_code_2': self.ship_defect.action_code_2,
                            'action_code_3': self.ship_defect.action_code_3,
                            'class_is_responsible':
                                self.ship_defect.class_is_responsible,
                            'defect_code': self.ship_defect.defect_code,
                            'defect_id': self.ship_defect.defect_id,
                            'defect_text': self.ship_defect.defect_text,
                            'detention_reason_deficiency':
                                self.ship_defect.detention_reason_deficiency,
                            'inspection':
                                f'/api/v1/inspections/'
                                f'{self.ship_defect.inspection.inspection_id}',
                            'main_defect_code':
                                self.ship_defect.main_defect_code,
                            'main_defect_text':
                                self.ship_defect.main_defect_text,
                            'other_action': self.ship_defect.other_action,
                            'other_recognised_org_resp':
                                self.ship_defect.other_recognised_org_resp,
                            'recognised_org_resp':
                                self.ship_defect.recognised_org_resp,
                            'recognised_org_resp_code':
                                self.ship_defect.recognised_org_resp_code,
                            'recognised_org_resp_yn':
                                self.ship_defect.recognised_org_resp_yn,
                            'resource_uri':
                                f'/api/v1/defects/{self.ship_defect.pk}'
                        }
                    ],
                    'detained': self.ship_inspection.detained,
                    'dwt': self.ship_inspection.dwt,
                    'expanded_inspection':
                        self.ship_inspection.expanded_inspection,
                    'flag_name': self.ship_inspection.flag_name,
                    'gt': self.ship_inspection.gt,
                    'imo_id': self.ship_inspection.imo_id,
                    'inspection_date': self.ship_inspection.inspection_date,
                    'inspection_id': self.ship_inspection.inspection_id,
                    'manager': self.ship_inspection.manager,
                    'no_days_detained': self.ship_inspection.no_days_detained,
                    'no_defects': self.ship_inspection.no_defects,
                    'number_part_days_detained':
                        str(self.ship_inspection.number_part_days_detained),
                    'other_inspection_type':
                        self.ship_inspection.other_inspection_type,
                    'owner': self.ship_inspection.owner,
                    'port_name': self.ship_inspection.port_name,
                    'resource_uri':
                        f'/api/v1/inspections/'
                        f'{self.ship_inspection.inspection_id}',
                    'ship_name': self.ship_inspection.ship_name,
                    'shipclass': self.ship_inspection.shipclass,
                    'shiptype': self.ship_inspection.shiptype,
                    'source': self.ship_inspection.source,
                    'yob': self.ship_inspection.yob
                },
            ]
        }

        data = json.loads(response.content)
        self.assertEqual(data, expected)
