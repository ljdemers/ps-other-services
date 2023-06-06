"""Screening API screeining bulk enums module"""
import enum


class BulkScreeningStatus(enum.Enum):
    DONE = '30-done'
    SCHEDULED = '40-scheduled'
    PENDING = '50-pending'
