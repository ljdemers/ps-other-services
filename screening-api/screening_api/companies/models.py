"""Screening API companies models module"""
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.types import Integer, String

from screening_api.models import BaseModel


class SISComplianceAssociation(BaseModel):

    __tablename__ = 'sis_compliance_association'
    __mapper_args__ = {
        'confirm_deleted_rows': False,
    }

    id = None
    sis_company_id = Column(
        Integer, ForeignKey('sis_companies.id'), primary_key=True)
    compliance_entity_id = Column(
        Integer, ForeignKey('compliance_entities.id'), primary_key=True)

    compliance_entity = relationship(
        "ComplianceEntity", backref="associations")


class SISCompany(BaseModel):

    __tablename__ = 'sis_companies'

    sis_code = Column(String, nullable=False, unique=True)
    name = Column(String)

    compliance = relationship(
        "ComplianceEntity",
        secondary="sis_compliance_association", backref="sis",
    )
