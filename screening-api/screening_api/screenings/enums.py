from enum import Enum


class ComparableEnum(Enum):

    def __str__(self):
        return self.value

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class Severity(ComparableEnum):
    OK = '20-ok'
    WARNING = '30-warning'
    CRITICAL = '40-critical'
    UNKNOWN = '50-unknown'


class SeverityChange(ComparableEnum):
    DECREASED = '10-decreased'
    NOCHANGE = '20-nochange'
    INCREASED = '30-increased'


class Status(ComparableEnum):
    CREATED = '20-created'
    DONE = '30-done'
    SCHEDULED = '40-scheduled'
    PENDING = '50-pending'

    @property
    def completed(self):
        completed_statuses = [self.CREATED, self.DONE]
        return self in completed_statuses
