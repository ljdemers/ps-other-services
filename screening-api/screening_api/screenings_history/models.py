"""Screening API screenings history models module"""
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, DateTime

from screening_api.models import BaseModel
from screening_api.screenings.models import ScreeningResult
from screening_api.screenings_reports.models import BaseScreeningReport


class ScreeningHistory(ScreeningResult, BaseScreeningReport, BaseModel):

    __tablename__ = 'screenings_history'

    severity_date = Column(DateTime, nullable=False)
    screening_id = Column(
        Integer,
        ForeignKey('screenings.id', onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    screening = relationship(
        "Screening",
        backref=backref("history", cascade="all, delete-orphan"),
    )

    @property
    def severity(self):
        return max([
            self.company_sanctions_severity, self.ship_sanctions_severity,
            self.country_sanctions_severity, self.ship_inspections_severity,
            self.ship_movements_severity,
        ])

    def __json__(self):
        return [
            'id', 'created', 'updated', 'screening_id', 'severity_date',
            'severity', 'company_sanctions_severity',
            'ship_sanctions_severity', 'country_sanctions_severity',
            'ship_inspections_severity', 'ship_movements_severity',
        ]
