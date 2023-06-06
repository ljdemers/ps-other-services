"""Screening API ship sanctions models module"""
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.types import Integer, Date, String, Boolean

from screening_api.models import BaseModel


class ShipSanction(BaseModel):

    __tablename__ = 'ship_sanctions'

    ship_id = Column(
        Integer,
        ForeignKey('ships.id', onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    code = Column(Integer, nullable=False)
    sanction_list_name = Column(String, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean)

    ship = relationship(
        "Ship",
        backref=backref("sanctions", cascade="all, delete-orphan"),
    )

    __table_args__ = (
        UniqueConstraint(
            'ship_id', 'sanction_list_name',
            name='ship_id_sanction_list_name',
        ),
    )
