"""Screening API testing providers module"""
from faker.providers import BaseProvider


class ReportsProvider(BaseProvider):

    def ship_info_report(self):
        return {
            'name': 'Karpaty Trader',
            'imo': '8836986',
            'type': 'Products Tanker',
            'build_year': 2000,
            'build_age': 20,
            'build_age_severity': 'WARNING',
            'country_name': 'Poland',
            'country_id': 'PL',
            'flag_effective_date': '',
            'mmsi': '99999999999',
            'call_sign': '',
            'status': '',
            'port_of_registry': '',
            'deadweight': 149834,
            'weight': 79979,
            'length': 269.0,
            'breadth': 46.0,
            'displacement': 171567,
            'draught': 16.858,
            'registered_owner': '',
            'operator': '',
            'group_beneficial_owner': '',
            'ship_manager': '',
            'technical_manager': '',
            'shipbuilder': '',
            'build_country_name': '',
            'classification_society': None,
        }

    def ship_registered_owner_company_report(self):
        return self.ship_associated_company_report()

    def ship_operator_company_report(self):
        return self.ship_associated_company_report()

    def ship_beneficial_owner_company_report(self):
        return self.ship_associated_company_report()

    def ship_manager_company_report(self):
        return self.ship_associated_company_report()

    def ship_technical_manager_company_report(self):
        return self.ship_associated_company_report()

    def ship_company_associates_report(self, num=4):
        associates = [self.ship_company_associate_report() for x in range(num)]
        return {
            'associates': associates,
        }

    def ship_company_associate_report(self, num=4):
        sanctions = [self.ship_company_sanction_report() for x in range(num)]
        return {
            'company_name': 'Company name',
            'relationship': 'relationship',
            'dst_type': 'organisation',
            'sanctions': sanctions,
        }

    def ship_company_sanction_report(self):
        return {
            'sanction_name': 'Sanction list name',
            'listed_since': '2017-05-15T00:00:00Z',
            'listed_to': '2017-05-15T00:00:00Z',
            'sanction_severity': 'WARNING',
        }

    def ship_association_report(self):
        return {}

    def ship_sanction_report(self):
        return {
            'sanctions': [
                {
                    'listed_since': '2012-07-12T00:00:00Z',
                    'listed_to': '2016-01-16T00:00:00Z',
                    'sanction_name': 'OFAC List',
                    'sanction_severity': 'OK',
                }
            ]
        }

    def ship_flag_report(self):
        return {
            "country": "Poland",
            "severity": "OK",
        }

    def ship_registered_owner_report(self):
        return self.ship_associated_country_report()

    def ship_operator_report(self):
        return self.ship_associated_country_report()

    def ship_beneficial_owner_report(self):
        return self.ship_associated_country_report()

    def ship_manager_report(self):
        return self.ship_associated_country_report()

    def ship_technical_manager_report(self):
        return self.ship_associated_country_report()

    def doc_company_report(self):
        return {}

    def ship_inspections_report(self, num=4):
        inspections = [self.ship_inspection_report() for x in range(num)]
        return {
            'inspections': inspections,
        }

    def zone_visits_report(self):
        return {}

    def ship_inspection_report(self):
        return {
            "inspection_date": "2001-09-11",
            "authority": "",
            "detained": True,
            "detained_days": 1.0,
            "detained_days_severity": "CRITICAL",
            "defects_count": 1,
            "defects_count_severity": "WARNING",
            "port_name": "Port Gdanski",
            "country_name": "Poland",
        }

    def ship_associated_company_report(self, num=4):
        sanctions = [self.ship_company_sanction_report() for x in range(num)]
        return {
            'company_name': 'Company name',
            'sanctions': sanctions,
        }

    def ship_associated_country_report(self):
        return {
            "country_of_domicile": "Poland",
            "country_of_domicile_severity": "WARNING",
            "country_of_control": "Great Britain",
            "country_of_control_severity": "CRITICAL",
            "country_of_registration": "USA",
            "country_of_registration_severity": "OK",
        }

    def ship_movements_report(self):
        return {
            "port_visits": [
                {
                    "departed": "2017-12-26T21:50:49Z",
                    "entered": "2017-12-26T21:50:49Z",
                    "port_name": "Abidjan SBM/MBM",
                    "port_latitude": None,
                    "port_code": "CIPBT",
                    "port_country_name": None,
                    "port_longitude": None,
                    "category": "US Port Authority",
                    "severity": "WARNING"
                },
            ],
            "ihs_movement_data": [
                {
                    "departed": "2017-12-26T21:50:49Z",
                    "destination_port_severity": "OK",
                    "last_port_of_call_country_code": "UA",
                    "destination_port": None,
                    "last_port_of_call_country": "Ukrain",
                    "last_port_of_call_severity": "OK",
                    "last_port_of_call_name": "Yokkaichi and Nagoya Anchorage",
                    "port_severity": "CRITICAL",
                    "country_name": "Japan",
                    "port_name": "Sevastopol",
                    "entered": "2017-12-26T21:50:49Z"
                }
            ]
        }


class ShipProvider(BaseProvider):

    def ship_status(self):
        return 'In Service/Commission'

    def ship_call_sign(self):
        return 'WCDP'
