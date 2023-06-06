"""Screening API sanctions models module"""
from datetime import date

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, Date, String, Enum

from screening_api.models import BaseModel
from screening_api.screenings.enums import Severity


class ComplianceEntitySanction(BaseModel):

    __tablename__ = 'compliance_entity_sanctions'

    compliance_id = Column(Integer, nullable=False, unique=True)
    compliance_sanction_id = Column(
        Integer,
        ForeignKey(
            'compliance_sanctions.id',
            onupdate="CASCADE", ondelete="CASCADE",
        ),
        nullable=False, index=True,
    )
    compliance_entity_id = Column(
        Integer,
        ForeignKey(
            'compliance_entities.id',
            onupdate="CASCADE", ondelete="CASCADE",
        ),
        nullable=False, index=True,
    )
    severity = Column(Enum(Severity), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    compliance_sanction = relationship(
        "ComplianceSanction", backref=backref(
            "entity_sanctions",
            collection_class=attribute_mapped_collection("severity"),
        ),
    )
    compliance_entity = relationship(
        "ComplianceEntity", backref='entity_sanctions')

    @property
    def is_active(self):
        today = date.today()
        if self.end_date and self.end_date < today:
            return False
        if self.start_date and self.start_date > today:
            return False
        return True

    @classmethod
    def creator(cls, id: int, data: dict):
        if data is None:
            data = {}

        return cls(compliance_entity_id=id, **data)


class ComplianceSanction(BaseModel):

    __tablename__ = 'compliance_sanctions'

    code = Column(Integer, nullable=False, unique=True)

    sanction_list_name = Column(String, nullable=False)

    entities = relationship(
        "ComplianceEntity",
        secondary="compliance_entity_sanctions", backref="sanctions",
    )

    compliance_entity_ids = association_proxy(
        "entity_sanctions", "compliance_entity_id",
        creator=ComplianceEntitySanction.creator)
