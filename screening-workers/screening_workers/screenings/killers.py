"""Screening workers screenings killers module"""
import logging
from datetime import datetime, timedelta

from screening_api.screenings.enums import Status, Severity
from screening_api.screenings.models import Screening
from screening_api.screenings.repositories import ScreeningsRepository

log = logging.getLogger(__name__)


class ScreeningKiller:

    CHECKS = [
        'ship_registered_owner_company',
        'ship_operator_company',
        'ship_beneficial_owner_company',
        'ship_manager_company',
        'ship_technical_manager_company',
        'ship_company_associates',
        'ship_association',
        'ship_sanction',
        'ship_flag',
        'ship_registered_owner',
        'ship_operator',
        'ship_beneficial_owner',
        'ship_manager',
        'ship_technical_manager',
        'doc_company',
        'ship_inspections',
        'port_visits',
        'zone_visits',
    ]

    UPDATED_TRESHOLD_TIMEDELTA = timedelta(hours=6)

    def __init__(
        self,
        screenings_repository: ScreeningsRepository,
    ):
        self.screenings_repository = screenings_repository

    def kill(self, screening_id: int):
        screening = self._get_screening(screening_id)

        if screening.status.completed:
            return

        self._set_screening_completed(screening)

        log.warning(
            'Killing screening: %s',
            screening_id
        )

    def _get_screening(self, screening_id: int) -> Screening:
        return self.screenings_repository.get(id=screening_id)

    def _set_screening_completed(self, screening: Screening) -> None:
        data = {}
        for check in self.CHECKS:
            check_data = self._contribute_check_to_update(screening, check)
            data.update(check_data)

        self.screenings_repository.update(screening.id, **data)

    def _get_check_status_field_name(self, name) -> str:
        assert name in self.CHECKS

        return '{0}_status'.format(name)

    def _get_check_severity_field_name(self, name) -> str:
        assert name in self.CHECKS

        return '{0}_severity'.format(name)

    def _get_screening_check_status(self, screening, check_name):
        field_name = self._get_check_status_field_name(check_name)

        return getattr(screening, field_name)

    def _get_screening_check_severity(self, screening, check_name):
        field_name = self._get_check_severity_field_name(check_name)

        return getattr(screening, field_name)

    def _contribute_check_to_update(self, screening, check):
        # check time condition
        now = datetime.utcnow()
        updated_treshold = now - self.UPDATED_TRESHOLD_TIMEDELTA
        if screening.updated > updated_treshold:
            return {}

        # check status condition
        status = self._get_screening_check_status(screening, check)
        if status.completed:
            return {}

        return {
            self._get_check_status_field_name(check):
                Status.DONE,
            self._get_check_severity_field_name(check):
                Severity.UNKNOWN,
        }
