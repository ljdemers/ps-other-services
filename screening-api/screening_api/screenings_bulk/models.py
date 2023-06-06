"""Screening API screenings bulk models module"""
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, Enum, String, Boolean

from screening_api.models import BaseModel
from screening_api.screenings_bulk.enums import BulkScreeningStatus


class BulkScreening(BaseModel):

    __tablename__ = 'screenings_bulk'

    account_id = Column(Integer, nullable=False, index=True)
    imo_id = Column(String, nullable=False)
    status = Column(
        Enum(BulkScreeningStatus), default=BulkScreeningStatus.SCHEDULED,
        nullable=False, index=True,
    )
    result = Column(Boolean, nullable=True, index=True)
