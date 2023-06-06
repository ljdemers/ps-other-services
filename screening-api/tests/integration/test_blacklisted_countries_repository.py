import pytest

from screening_api.blacklisted_countries.repositories import (
    BlacklistedCountriesRepository,
)
from screening_api.screenings.enums import Severity


class TestAssociatedCountriesSeverities:

    @pytest.fixture
    def repository(self, session_factory):
        return BlacklistedCountriesRepository(session_factory)

    @pytest.mark.parametrize('country_critical_1,country_critical_2', [
        ('Korea, North', 'Iran'), ('Cuba', 'Syrian Arab Republic'),
    ])
    def test_initial_blacklisted_countries(
            self, repository, country_critical_1, country_critical_2):
        country_ok = 'UK'

        result = repository.get_associated_countries_severities(
            country_ok, country_critical_1, country_critical_2)

        assert result == (Severity.OK, Severity.CRITICAL, Severity.CRITICAL)

    def test_country_name_with_apostrophe_escape(self, repository):
        country_ok = "Cote d'Ivoire"

        result = repository.get_associated_countries_severities(
            country_ok, country_ok, country_ok)

        assert result == (Severity.OK, Severity.OK, Severity.OK)
