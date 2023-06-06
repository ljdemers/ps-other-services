"""Screening API entities repositories module"""
from screening_api.lib.alchemy.repositories import AlchemyRepository
from screening_api.entities.models import ComplianceEntity


class ComplianceEntitiesRepository(AlchemyRepository):

    model = ComplianceEntity
