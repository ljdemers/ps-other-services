from jsonschema.exceptions import ValidationError
import pytest

from screening_api.main import get_json_content, get_resource_fullpath
from screening_api.screenings.enums import Severity
from screening_api.screenings_reports.validators import ReportSchemaValidator


class TestShipAssociatedCountryReportSchema:

    @pytest.fixture
    def schema(self):
        return get_json_content('spec/ship_associated_country_report.json')

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
            'country_of_domicile_severity': 'Atlantis',
        }

        with pytest.raises(ValidationError):
            validator.validate(data)

    def test_valid(self, validator):
        data = {
            'country_of_domicile': 'Poland',
            'country_of_domicile_severity': Severity.UNKNOWN.name,
            'country_of_control': 'Great Britain',
            'country_of_control_severity': Severity.WARNING.name,
            'country_of_registration': 'USA',
            'country_of_registration_severity': Severity.CRITICAL.name,
        }

        validator.validate(data)
