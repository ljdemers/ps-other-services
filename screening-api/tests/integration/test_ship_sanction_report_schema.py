from jsonschema.exceptions import ValidationError
import pytest

from screening_api.main import get_json_content, get_resource_fullpath
from screening_api.screenings.enums import Severity
from screening_api.screenings_reports.validators import ReportSchemaValidator


class TestShipSanctionReportSchema:

    @pytest.fixture
    def schema(self):
        return get_json_content('spec/ship_sanction_report.json')

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
            'sanctions': {},
        }

        with pytest.raises(ValidationError):
            validator.validate(data)

    def test_valid(self, validator):
        data = {
            'sanctions': [
                {
                    'sanction_name': 'Sanction List',
                    'listed_since': '2001-09-11',
                    'listed_to': '2001-09-12',
                    'sanction_severity': Severity.UNKNOWN.name,
                },
            ],
        }

        validator.validate(data)

    def test_null_dates(self, validator):
        data = {
            'sanctions': [
                {
                    'sanction_name': 'Sanction List',
                    'listed_since': None,
                    'listed_to': None,
                    'sanction_severity': Severity.OK.name,
                },
            ],
        }

        validator.validate(data)
