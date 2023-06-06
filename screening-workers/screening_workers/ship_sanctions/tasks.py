from screening_workers.lib.screening.tasks import CheckTask


class ShipAssociationCheckTask(CheckTask):

    name = 'screening.ship_sanctions.ship_association_check'


class ShipSanctionCheckTask(CheckTask):

    name = 'screening.ship_sanctions.ship_sanction_check'
