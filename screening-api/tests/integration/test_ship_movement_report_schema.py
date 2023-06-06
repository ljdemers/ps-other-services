from jsonschema.exceptions import ValidationError
import pytest

from screening_api.main import get_json_content, get_resource_fullpath
from screening_api.screenings.enums import Severity
from screening_api.screenings_reports.validators import ReportSchemaValidator


class TestShipMovementReportSchema:

    @pytest.fixture
    def schema(self):
        return get_json_content('spec/ship_movement_report.json')

    @pytest.fixture
    def spec_path(self):
        return get_resource_fullpath('spec/')

    @pytest.fixture
    def validator(self, schema, spec_path):
        return ReportSchemaValidator(schema, spec_path)

    def test_empty(self, validator):
        data = {}

        validator.validate(data)

    def test_invalid_property_schema(self, validator):
        data = {
            "port_visits": {},
        }

        with pytest.raises(ValidationError):
            validator.validate(data)

    def test_valid(self, validator):
        data = {
            "port_visits": [
                {
                    "departed": "2018-03-02T14:05:00Z",
                    "entered": "2018-03-02T09:39:20Z",
                    "port_name": "Abidjan SBM/MBM",
                    "port_latitude": 5.233333110809326,
                    "port_code": "CIPBT",
                    "port_country_name": "C\u00f4te d'Ivoire",
                    "port_longitude": -3.9666666984558105,
                    "category": None,
                    "severity": Severity.OK.name
                },
            ],
            "ihs_movement_data": [
                {
                    "departed": "2018-01-06T11:56:12Z",
                    "destination_port_severity": Severity.OK.name,
                    "last_port_of_call_country_code": "UA",
                    "destination_port": "Reni",
                    "last_port_of_call_country": "Ukrain",
                    "last_port_of_call_severity": Severity.OK.name,
                    "last_port_of_call_name": "Yokkaichi and Nagoya Anchorage",
                    "port_severity": Severity.WARNING.name,
                    "country_name": "Japan",
                    "port_name": "Sevastopol",
                    "entered": "2017-12-26T21:50:49Z"
                }
            ]
        }

        validator.validate(data)

    def test_null_data(self, validator):
        data = {
            "port_visits": [
                {
                    "departed": None,
                    "entered": None,
                    "port_name": "Abidjan SBM/MBM",
                    "port_latitude": None,
                    "port_code": "CIPBT",
                    "port_country_name": None,
                    "port_longitude": None,
                    "category": "US Port Authority",
                    "severity": Severity.WARNING.name
                },
            ],
            "ihs_movement_data": [
                {
                    "departed": None,
                    "destination_port_severity": Severity.OK.name,
                    "last_port_of_call_country_code": "UA",
                    "destination_port": None,
                    "last_port_of_call_country": "Ukrain",
                    "last_port_of_call_severity": Severity.OK.name,
                    "last_port_of_call_name": "Yokkaichi and Nagoya Anchorage",
                    "port_severity": Severity.CRITICAL.name,
                    "country_name": "Japan",
                    "port_name": "Sevastopol",
                    "entered": "2017-12-26T21:50:49Z"
                }
            ]
        }
        validator.validate(data)
