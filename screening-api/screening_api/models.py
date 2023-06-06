"""Screening API models module"""
from datetime import datetime

from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, DateTime

from sqlalchemy.ext.declarative import declarative_base


class Base:

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,
        nullable=False,
    )


BaseModel = declarative_base(cls=Base)
