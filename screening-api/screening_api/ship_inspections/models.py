"""Screening API checks models module"""
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, Float, Date, String, Boolean

from screening_api.models import BaseModel


class ShipInspection(BaseModel):

    __tablename__ = 'ship_inspections'

    ship_id = Column(
        Integer,
        ForeignKey('ships.id', onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    inspection_id = Column(String, nullable=False, unique=True)
    inspection_date = Column(Date, nullable=False)
    authority = Column(String, nullable=False)
    detained = Column(Boolean, nullable=False, default=False)
    detained_days = Column(Float, nullable=False)  # Float from SIS
    defects_count = Column(Integer, nullable=False)
    port_name = Column(String, nullable=True)
    country_name = Column(String, nullable=True)

    ship = relationship(
        "Ship",
        backref=backref("inspections", cascade="all, delete-orphan"),
    )

    @property
    def calculated_detained(self):
        return bool(self.detained_days)

    @property
    def deficiency(self):
        return bool(self.defects_count)
