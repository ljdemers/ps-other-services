from jsonschema.exceptions import ValidationError
import pytest

from screening_api.main import get_json_content, get_resource_fullpath
from screening_api.screenings.enums import Severity
from screening_api.screenings_reports.validators import ReportSchemaValidator


class TestShipInspectionsReportSchema:

    @pytest.fixture
    def schema(self):
        return get_json_content('spec/ship_inspections_report.json')

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
            'inspections': {},
        }

        with pytest.raises(ValidationError):
            validator.validate(data)

    def test_valid(self, validator):
        data = {
            'inspections': [
                {
                    'inspection_date': '2001-09-11',
                    'authority': 'US Coastguard',
                    'port_name': 'Gdansk',
                    'country_name': 'Poland',
                    'detained_days': 1.2,
                    'detained_days_severity': Severity.UNKNOWN.name,
                    'defects_count': 1,
                    'defects_count_severity': Severity.OK.name,
                },
            ],
        }

        validator.validate(data)
