"""Screening API blacklisted countries repositories module"""
from typing import Tuple

from sqlalchemy import text

from screening_api.lib.alchemy.repositories import AlchemyRepository
from screening_api.blacklisted_countries.models import BlacklistedCountry
from screening_api.screenings.enums import Severity


class BlacklistedCountriesRepository(AlchemyRepository):

    model = BlacklistedCountry

    def create(
            self, country_id: str, country_name: str,
            **kwargs,
    ) -> BlacklistedCountry:
        kwargs.update({
            'country_id': country_id,
            'country_name': country_name,
        })

        return super(BlacklistedCountriesRepository, self).create(**kwargs)

    def get_associated_countries_severities(
        self,
        country_of_domicile: str, country_of_control: str,
        country_of_registration: str,
        **options,
    ) -> Tuple[Severity]:
        session = options.pop('session', None)
        if session is None:
            session = self.get_session()

        result = session.execute(
            text("""
SELECT
    COALESCE (bc1.severity, 'OK'::severity)
        AS country_of_domicile_severity,
    COALESCE (bc2.severity, 'OK'::severity)
        AS country_of_control_severity,
    COALESCE (bc3.severity, 'OK'::severity)
        AS country_of_registration_severity
FROM
(
    VALUES (
        :country_of_domicile , :country_of_control , :country_of_registration
    )
) as i(
    country_of_domicile,
    country_of_control,
    country_of_registration
)
LEFT JOIN blacklisted_countries AS bc1
ON bc1.country_name = i.country_of_domicile
LEFT JOIN blacklisted_countries AS bc2
ON bc2.country_name = i.country_of_control
LEFT JOIN blacklisted_countries AS bc3
ON bc3.country_name = i.country_of_registration
            """),
            dict(
                country_of_domicile=country_of_domicile,
                country_of_control=country_of_control,
                country_of_registration=country_of_registration,
            )
        ).fetchone()

        return tuple(map(Severity.__getitem__, result))
