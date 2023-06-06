"""Screening Workers company sanctions tasks module"""
from screening_workers.lib.screening.tasks import CheckTask


class BaseCompanySanctionsCheckTask(CheckTask):
    pass


class ShipRegisteredOwnerCompanyCheckTask(BaseCompanySanctionsCheckTask):

    name = 'screening.company_sanctions.ship_registered_owner_check'


class ShipOperatorCompanyCheckTask(BaseCompanySanctionsCheckTask):

    name = 'screening.company_sanctions.ship_operator_check'


class ShipBeneficialOwnerCompanyCheckTask(BaseCompanySanctionsCheckTask):

    name = 'screening.company_sanctions.ship_beneficial_owner_check'


class ShipManagerCompanyCheckTask(BaseCompanySanctionsCheckTask):

    name = 'screening.company_sanctions.ship_manager_check'


class ShipTechnicalManagerCompanyCheckTask(BaseCompanySanctionsCheckTask):

    name = 'screening.company_sanctions.ship_technical_manager_check'


class ShipCompanyAssociatesCheckTask(BaseCompanySanctionsCheckTask):

    name = 'screening.company_sanctions.ship_company_associates_check'
