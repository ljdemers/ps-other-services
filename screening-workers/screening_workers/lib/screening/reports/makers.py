from screening_workers.lib.screening.providers import DataProvider
from screening_workers.lib.screening.reports.models import Report


class CheckReportMaker:

    def make_report(self, data_provider: DataProvider) -> Report:
        raise NotImplementedError
