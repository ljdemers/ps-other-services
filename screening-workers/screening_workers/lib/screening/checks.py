import logging
import time
from abc import ABC

from sqlalchemy.orm.session import Session

from screening_workers.lib.utils import json_logger

from screening_api.screenings.enums import Severity, Status
from screening_api.screenings.models import Screening
from screening_api.screenings.repositories import ScreeningsRepository
from screening_api.screenings_reports.models import ScreeningReport
from screening_api.screenings_reports.repositories import (
    ScreeningsReportsRepository,
)

from screening_workers.lib.screening.providers import DataProvider
from screening_workers.lib.screening.reports.models import Report

log = logging.getLogger(__name__)


class CheckInterface(ABC):
    """
    Screening check Interface.
    """
    def do_check(self, screening_id: int) -> None:
        """
        Perform the relevant check.

        Args:
            screening_id: ID for a screening instance
        """
        raise NotImplementedError

    def on_failure(self, screening_id: int) -> None:
        """
        Clean up after relevant check.

        Args:
            screening_id: ID for a screening instance
        """
        raise NotImplementedError


class BaseCheck(CheckInterface):
    """
    Base check functionality.
    """

    name = NotImplemented

    def __init__(self, screenings_repository: ScreeningsRepository):
        self.screenings_repository = screenings_repository
        self.logger = json_logger(__name__, level='INFO')

    def do_check(self, screening_id: int) -> None:
        """
        Perform a given check as part of a screening.

        Manage the screening status around main body of check.

        Args:
            screening_id: ID of a screening instance
        """
        screening = self._get_screening_or_none(screening_id)
        if screening is None:
            log.warning("Screening not found. Skipping")
            return

        self._set_screening_check_status_pending(screening.id)

        self.logger.info("Check started",
                         name=self.name,
                         screening=screening_id)
        st = time.monotonic()
        severity = self.process(screening)
        self.logger.info("Check completed",
                         name=self.name,
                         screening=screening_id,
                         severity=severity,
                         elapsed=time.monotonic() - st)
        self._set_screening_check_status_done(screening.id, severity)

    def process(self, screening: Screening) -> Severity:
        """
        The main body of the check, to be overridden.

        Args:
            screening: A screening instance

        Returns:
            Severity of the check
        """
        raise NotImplementedError

    def on_failure(self, screening_id: int) -> None:
        """
        Update screening if a failure has occurred.

        Args:
            screening_id: ID of a screening instance
        """
        self.logger.warning("Check Failed", screening_id=screening_id)
        self._set_screening_check_status_done(screening_id, Severity.UNKNOWN)

    def _get_screening_or_none(self, screening_id: int) -> Screening:
        return self.screenings_repository.get_or_none(
            id=screening_id, joinedload_related=['ship'])

    def _get_check_status_field_name(self) -> str:
        return '{0}_status'.format(self.name)

    def _get_check_severity_field_name(self) -> str:
        return '{0}_severity'.format(self.name)

    def _set_screening_check_status_pending(self, screening_id: int):
        status_field_name = self._get_check_status_field_name()
        data = {status_field_name: Status.PENDING}
        return self.screenings_repository.update(screening_id, **data)

    def _set_screening_check_status_done(
            self, screening_id: int, severity: Severity) -> Screening:
        status_field_name = self._get_check_status_field_name()
        severity_field_name = self._get_check_severity_field_name()
        data = {status_field_name: Status.DONE, severity_field_name: severity}
        self.logger.info(data)
        return self.screenings_repository.update(screening_id, **data)


class ReportCheck(BaseCheck):
    """
    Perform a screening check using a report

    A report object can be used to extract relevant information from the
    provided check data.
    """

    def __init__(
            self,
            screenings_repository: ScreeningsRepository,
            screenings_reports_repository: ScreeningsReportsRepository,
    ):
        super(ReportCheck, self).__init__(screenings_repository)
        self.screenings_reports_repository = screenings_reports_repository

    def process(
            self,
            screening: Screening,
            session: Session = None,
    ) -> Severity:
        data_provider = self.get_data_provider(screening)
        check_report = self.make_report(data_provider)

        session = session or self._get_session()
        screening_report = self._get_or_create_plain_report(
            data_provider, session)

        self._set_check_report(screening_report, check_report, session)
        return check_report.severity

    def get_data_provider(self, screening: Screening) -> DataProvider:
        """
        Generate a data provider for a given screening.
        """
        return DataProvider(screening)

    def make_report(self, data_provider: DataProvider) -> Report:
        """
        Generate a check report for a given set of data.
        """
        raise NotImplementedError

    def _get_session(self):
        return self.screenings_reports_repository.get_session()

    def _get_plain_report_data(self) -> dict:
        return {
            'ship_inspections': {},
        }

    def _get_or_create_plain_report(
            self,
            data_provider: DataProvider,
            session: Session,
    ) -> Report:
        plain_report = self._get_plain_report_data()

        report, _ = self.screenings_reports_repository.get_or_create(
            screening_id=data_provider.screening.id,
            create_kwargs=plain_report,
            session=session,
        )
        assert report.id

        return report

    def _get_check_report_field_name(self) -> str:
        return self.name

    def _set_check_report(
            self,
            screening_report: ScreeningReport,
            check_report: Report,
            session: Session,
    ):
        check_report_field_name = self._get_check_report_field_name()
        data = {check_report_field_name: check_report.asdict()}
        self.screenings_reports_repository.update(
            screening_report, **data, session=session)
