from screening_api.screenings.enums import Severity


class DefaultScreeningProfile:

    ship_last_inspection_detained_severity = Severity.CRITICAL
    ship_once_detained_in_24_months_severity = Severity.OK
    ship_1_or_more_detained_in_12_months_severity = Severity.WARNING
    ship_1_or_more_detained_in_12_months_ca_severity = Severity.CRITICAL
    ship_2_or_more_detained_in_12_months_severity = Severity.CRITICAL
    ship_2_or_more_detained_in_24_months_severity = Severity.OK
    ship_detained_in_over_24_months_severity = Severity.OK
    ship_deficiency_severity = Severity.OK
    ship_active_sanction_severity = Severity.CRITICAL
    company_active_sanction_severity = Severity.WARNING
    unknown_country_of_domicile_severity = Severity.OK
    unknown_country_of_control_severity = Severity.OK
    unknown_country_of_registration_severity = Severity.OK

    blacklisted_sanction_list_id = 1
