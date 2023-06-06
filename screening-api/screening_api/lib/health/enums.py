from enum import Enum


class HealthStatus(Enum):

    DISABLED = 'disabled'
    PASSING = 'passing'
    WARNING = 'warning'
    FAILING = 'failing'
