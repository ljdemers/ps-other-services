import pytest
from openapi_spec_validator import validate_spec

from screening_api.main import get_json_content


class TestOpenAPISpec:

    @pytest.fixture
    def spec_dict(self):
        return get_json_content('spec/openapi.json')

    def test_valid(self, spec_dict):
        validate_spec(spec_dict)
