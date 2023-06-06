"""Screening API screenings writers module"""
from csv import writer, excel
from io import StringIO
from typing import List

from screening_api.screenings.models import Screening


class ScreeningsCSVWriter:

    delimiter = ','
    quotechar = '"'
    dialect = excel
    datetime_format = "%Y-%m-%dT%H:%M:%S"

    def __init__(self, content: StringIO):
        self.writer = writer(
            content,
            delimiter=self.delimiter, quotechar=self.quotechar,
            dialect=self.dialect,
        )

    def write(self, screenings: List[Screening]) -> None:
        self.write_header_row()
        list(map(self.write_screening_row, screenings))

    def write_header_row(self):
        row = self._get_header_row()
        self.writer.writerow(row)

    def write_screening_row(self, screening: Screening) -> None:
        row = self._get_screening_row(screening)
        self.writer.writerow(row)

    def _get_header_row(self):
        return [
            'Flag', 'Ship Name',
            'IMO', 'Ship Type',
            'Current Result', 'Previous severity',
            'Previous severity date (UTC)',
            'Last Updated (UTC)',
        ]

    def _get_screening_row(self, screening: Screening) -> bytes:
        previous_severity = None
        if screening.previous_severity is not None:
            previous_severity = screening.previous_severity.name

        previous_severity_date = None
        if screening.previous_severity_date is not None:
            previous_severity_date = screening.previous_severity_date.strftime(
                self.datetime_format)

        updated = screening.updated.strftime(self.datetime_format)
        return [
            screening.ship.country_name, screening.ship.name,
            screening.ship.imo_id, screening.ship.type,
            screening.result, previous_severity,
            previous_severity_date, updated,
        ]
