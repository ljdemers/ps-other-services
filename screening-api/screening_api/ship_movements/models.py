"""Screening API checks models module"""
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, Date, String

from screening_api.models import BaseModel


class ShipPortVisit(BaseModel):

    __tablename__ = 'ship_port_visit'

    ship_id = Column(
        Integer,
        ForeignKey('ships.id', onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    movement_id = Column(Integer, nullable=False, unique=True)
    entered = Column(Date, nullable=True)
    departed = Column(Date, nullable=True)
    port_name = Column(String, nullable=True)
    port_code = Column(String, nullable=True)
    country_name = Column(String, nullable=True)
    country_code = Column(String, nullable=True)

    ship = relationship(
        "Ship",
        backref=backref("movements", cascade="all, delete-orphan"),
    )
