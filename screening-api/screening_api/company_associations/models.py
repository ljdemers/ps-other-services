"""Screening API company associations models module"""
from sqlalchemy.orm import relationship as column_relationship
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.types import Integer, String

from screening_api.models import BaseModel


class CompanyAssociation(BaseModel):

    __tablename__ = 'company_associations'

    src_id = Column(
        Integer,
        ForeignKey(
            'compliance_entities.id',
            onupdate="CASCADE", ondelete="CASCADE",
        ),
        nullable=False, index=True,
    )
    dst_id = Column(
        Integer,
        ForeignKey(
            'compliance_entities.id',
            onupdate="CASCADE", ondelete="CASCADE",
        ),
        nullable=False, index=True,
    )
    relationship = Column(String(), nullable=False)

    src = column_relationship("ComplianceEntity", foreign_keys=[src_id])
    dst = column_relationship("ComplianceEntity", foreign_keys=[dst_id])

    __table_args__ = (
        UniqueConstraint('src_id', 'dst_id', name='src_id_dst_id_unique'),
    )
