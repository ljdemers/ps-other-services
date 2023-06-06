"""Screening workers screenings schedulers module"""
import logging

from screening_api.screenings.enums import Status
from screening_api.screenings.models import Screening
from screening_api.screenings.repositories import ScreeningsRepository

from screening_workers.lib.screening.registries import CheckTasksRegistry
from screening_workers.screenings.creators import ScreeningsCreator
from screening_workers.screenings_history.creators import (
    ScreeningsHistoryCreator,
)

log = logging.getLogger(__name__)


class ScreeningScheduler:

    def __init__(
        self,
        screenings_repository: ScreeningsRepository,
        screenings_history_creator: ScreeningsHistoryCreator,
        check_tasks_registry: CheckTasksRegistry,
    ):
        self.screenings_repository = screenings_repository
        self.screenings_history_creator = screenings_history_creator
        self.check_tasks_registry = check_tasks_registry

    def schedule(self, screening_id: int):
        screening = self._get_screening(screening_id)

        if not screening.status.completed:
            log.warning('Screening ID <%s> not completed', screening.id)
            return

        self.screenings_history_creator.create(screening_id)
        self._set_screening_scheduled(screening)

        log.info(
            'Scheduling screening: %s',
            screening_id
        )
        for task in self.check_tasks_registry.values():
            task.apply_async((screening_id, ))

    def schedule_on_signal(
            self, sender: ScreeningsCreator, instance: Screening):
        self.schedule(instance.id)

    def _get_screening(self, screening_id: int) -> Screening:
        return self.screenings_repository.get(id=screening_id)

    def _set_screening_scheduled(self, screening: Screening) -> None:
        status = Status.SCHEDULED

        self.screenings_repository.update(
            screening.id,

            ship_registered_owner_company_status=status,
            ship_operator_company_status=status,
            ship_beneficial_owner_company_status=status,
            ship_manager_company_status=status,
            ship_technical_manager_company_status=status,
            ship_company_associates_status=status,
            ship_association_status=status,
            ship_sanction_status=status,
            ship_flag_status=status,
            ship_registered_owner_status=status,
            ship_operator_status=status,
            ship_beneficial_owner_status=status,
            ship_manager_status=status,
            ship_technical_manager_status=status,
            doc_company_status=status,
            ship_inspections_status=status,
            port_visits_status=status,
            zone_visits_status=status,
        )
