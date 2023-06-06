from jsonschema.exceptions import ValidationError
import pytest

from screening_api.main import get_json_content, get_resource_fullpath
from screening_api.screenings.enums import Severity
from screening_api.screenings_reports.validators import ReportSchemaValidator


class TestShipFlagReportSchema:

    @pytest.fixture
    def schema(self):
        return get_json_content('spec/ship_flag_report.json')

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
            'severity': 'Atlantis',
        }

        with pytest.raises(ValidationError):
            validator.validate(data)

    def test_valid(self, validator):
        data = {
            'country': 'Poland',
            'severity': Severity.UNKNOWN.name,
        }

        validator.validate(data)
