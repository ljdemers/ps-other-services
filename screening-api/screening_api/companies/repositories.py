"""Screening API companies repositories module"""
from screening_api.lib.alchemy.repositories import AlchemyRepository
from screening_api.companies.models import SISCompany


class SISCompaniesRepository(AlchemyRepository):

    model = SISCompany
