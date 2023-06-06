"""Screening API screenings bulk readers module"""
from csv import reader, excel
from typing import Generator, List

from screening_api.screenings_bulk.recorders import RecorderError


class BulkScreeningCSVReaderError(Exception):
    pass


class BulkScreeningCSVReader:

    delimiter = ','
    quotechar = '"'
    dialect = excel

    def __init__(self, content: str) -> None:
        self.reader = reader(
            content, delimiter=self.delimiter, quotechar=self.quotechar,
            dialect=self.dialect,
        )

    def read_imo_ids(self) -> List[int]:
        try:
            return list(self.read_row(0))
        except RecorderError as exc:
            raise BulkScreeningCSVReaderError(str(exc))

    def read_row(self, index: int = 0) -> Generator:
        for row in self.reader:
            yield row[index]
