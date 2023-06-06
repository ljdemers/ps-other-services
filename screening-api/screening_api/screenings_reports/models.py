"""Screening API screenings reports models module"""
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, JSON

from screening_api.models import BaseModel


class BaseScreeningReport:

    ship_info = Column(JSON())

    ship_registered_owner_company = Column(JSON())
    ship_operator_company = Column(JSON())
    ship_beneficial_owner_company = Column(JSON())
    ship_manager_company = Column(JSON())
    ship_technical_manager_company = Column(JSON())
    ship_company_associates = Column(JSON())

    ship_association = Column(JSON())
    ship_sanction = Column(JSON())

    ship_flag = Column(JSON())
    ship_registered_owner = Column(JSON())
    ship_operator = Column(JSON())
    ship_beneficial_owner = Column(JSON())
    ship_manager = Column(JSON())
    ship_technical_manager = Column(JSON())
    doc_company = Column(JSON())

    ship_inspections = Column(JSON())

    port_visits = Column(JSON())
    zone_visits = Column(JSON())


class ScreeningReport(BaseScreeningReport, BaseModel):

    __tablename__ = 'screenings_reports'

    screening_id = Column(
        Integer,
        ForeignKey('screenings.id', onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False, unique=True,
    )

    screening = relationship(
        "Screening",
        backref=backref("report", cascade="all, delete-orphan", uselist=False),
    )
