from enum import Enum


class MetricsEvent(Enum):
    TASK_RETRY = 'TaskRetry'
    TASK_SUCCESS = 'TaskSuccess'
    TASK_FAILURE = 'TaskFailure'
    TASK_REVOKED = 'TaskRevoked'
    TASK_TIME = 'TaskTime'
