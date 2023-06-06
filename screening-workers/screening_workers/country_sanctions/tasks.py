"""Screening Workers country sanctions tasks module"""
from screening_workers.lib.screening.tasks import CheckTask


class ShipFlagCheckTask(CheckTask):

    name = 'screening.country_sanctions.ship_flag_check'


class ShipRegisteredOwnerCheckTask(CheckTask):

    name = 'screening.country_sanctions.ship_registered_owner_check'


class ShipOperatorCheckTask(CheckTask):

    name = 'screening.country_sanctions.ship_operator_check'


class ShipBeneficialOwnerCheckTask(CheckTask):

    name = 'screening.country_sanctions.ship_beneficial_owner_check'


class ShipManagerCheckTask(CheckTask):

    name = 'screening.country_sanctions.ship_manager_check'


class ShipTechnicalManagerCheckTask(CheckTask):

    name = 'screening.country_sanctions.ship_technical_manager_check'


class DocCompanyCheckTask(CheckTask):

    name = 'screening.country_sanctions.doc_company_check'
